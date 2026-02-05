import os
import sys
import json
import time
import requests
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inkeep_core.extractor import ConfigExtractor
from inkeep_core.registry import SiteRegistry
from inkeep_core.client import InkeepClient

GITHUB_TOKEN = os.environ.get("MINER_TOKEN") or os.environ.get("GITHUB_TOKEN")
STATE_FILE = Path("github_miner/state.json")
MAX_RUNTIME_SECONDS = 45 * 60 

# 用于保护文件写入的锁
registry_lock = threading.Lock()

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            if "last_gradient" not in state: state["last_gradient"] = 1000
            if "max_stars" not in state: state["max_stars"] = 500000
            if "scanned_domains" not in state: state["scanned_domains"] = []
            return state
    return {"max_stars": 500000, "scanned_domains": [], "found_sites": [], "last_gradient": 1000}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_rate_limit(res):
    try:
        remaining = int(res.headers.get("x-ratelimit-remaining", 10))
        limit = int(res.headers.get("x-ratelimit-limit", 30))
        reset_time = int(res.headers.get("x-ratelimit-reset", time.time() + 60))
        buffer = max(3, int(limit * 0.1))
        if remaining <= buffer:
            sleep_seconds = reset_time - time.time() + 5
            print(f"⚠️ Rate limit low ({remaining}/{limit}). Sleeping for {sleep_seconds:.0f}s...", flush=True)
            if sleep_seconds > 0: time.sleep(sleep_seconds)
    except: pass

def search_github(state):
    max_stars = state["max_stars"]
    gradient = state.get("last_gradient", 1000)
    if max_stars < 10:
        print("Stars floor reached.", flush=True)
        return [], 500000, 1000

    if max_stars == 500000:
        query = "stars:24000..500000 pushed:>=2025-11-04 fork:false archived:false"
        print(f"🔍 [Bootstrap 1] Query: {query}", flush=True)
    elif max_stars == 24000:
        query = "stars:23000..24000 pushed:>=2025-11-04 fork:false archived:false"
        print(f"🔍 [Bootstrap 2] Query: {query}", flush=True)
    else:
        min_stars = max(0, max_stars - gradient)
        query = f"stars:{min_stars}..{max_stars} archived:false fork:false"
        print(f"🔍 [Dynamic] Query: {query} (Gradient: {gradient})", flush=True)

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 100, "page": 1}
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {GITHUB_TOKEN}"}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code == 422:
            print(f"❌ API Error 422: Invalid Query.", flush=True)
            return [], max_stars - gradient, gradient
        if res.status_code in [403, 429]:
            check_rate_limit(res)
            return search_github(state) 
        if res.status_code != 200:
            print(f"❌ API Error {res.status_code}", flush=True)
            return [], max_stars, gradient

        check_rate_limit(res)
        items = res.json().get("items", [])
        if not items:
            return [], max_stars - gradient, gradient * 2
            
        first, last = items[0]["stargazers_count"], items[-1]["stargazers_count"]
        print(f"   Result: Count={len(items)}, Top={first}, Bottom={last}", flush=True)
        
        next_max = last
        if next_max == max_stars: next_max -= 1
        
        if len(items) < 100:
            next_gradient = int(gradient * 1.5)
        else:
            next_gradient = max(100, first - last)

        return items, next_max, next_gradient
    except Exception as e:
        print(f"❌ Exception: {e}", flush=True)
        return [], max_stars, gradient

def verify_site_chat(url):
    try:
        client = InkeepClient(url)
        for chunk in client.ask("Hello"):
            if "[Error]" in chunk: return False
            return True
    except: return False
    return False

def update_registry_file(new_site):
    with registry_lock: # 加锁保护文件写入
        # 1. 更新 Python Registry
        py_file = Path("inkeep_core/registry.py")
        with open(py_file, 'r') as f: content = f.read()
        alias, url, desc = new_site['alias'], new_site['url'], new_site['desc']
        if f'"{alias}"' in content: return
        tag = "} # END_DEFAULT_SITES"
        tag_index = content.find(tag)
        if tag_index != -1:
            prefix = content[:tag_index].rstrip()
            suffix = content[tag_index:]
            if not prefix.endswith(","): prefix += ","
            entry = f'\n    "{alias}": {{\n        "url": "{url}",\n        "description": "{desc}"\n    }}'
            with open(py_file, 'w') as f: f.write(prefix + entry + "\n" + suffix)
            print(f"🎉 Python Code Updated: Added {alias}", flush=True)

        # 2. 更新 TypeScript Registry (Web)
        ts_file = Path("web/src/lib/inkeep/registry.ts")
        if ts_file.exists():
            with open(ts_file, 'r') as f: ts_content = f.read()
            if f'"{alias}"' not in ts_content:
                ts_tag = "};"
                ts_tag_index = ts_content.rfind(ts_tag)
                if ts_tag_index != -1:
                    ts_prefix = ts_content[:ts_tag_index].rstrip()
                    ts_suffix = ts_content[ts_tag_index:]
                    if not ts_prefix.endswith(","): ts_prefix += ","
                    ts_entry = f'\n  "{alias}": {{\n    url: "{url}",\n    description: "{desc}"\n  }}'
                    with open(ts_file, 'w') as f: f.write(ts_prefix + ts_entry + "\n" + ts_suffix)
                    print(f"🌐 Web Code Updated: Added {alias}", flush=True)

def update_readmes():
    with registry_lock: # 加锁保护文档更新
        import importlib
        import inkeep_core.registry
        importlib.reload(inkeep_core.registry)
        sites = inkeep_core.registry.DEFAULT_SITES
        for readme_file in ["README.md", "README_zh.md"]:
            if not os.path.exists(readme_file): continue
            is_zh = "zh" in readme_file
            md_lines = []
            for alias, info in sites.items():
                name = alias.capitalize()
                desc = info['description']
                if is_zh and (desc.startswith("Docs for ") or desc.startswith("Official docs for ")):
                    desc = desc.replace("Docs for ", "").replace("Official docs for ", "") + " 官方文档"
                md_lines.append(f"*   **{name}** ({desc})")
            
            md_content = "\n".join(md_lines)
            with open(readme_file, 'r') as f: text = f.read()
            pattern = r"(<!-- AUTO-GENERATED-SITES:START -->)(.*?)(<!-- AUTO-GENERATED-SITES:END -->)"
            replacement = f"\\1\n{md_content}\n\\3"
            new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)
            with open(readme_file, 'w') as f: f.write(new_text)
            print(f"📝 Updated {readme_file}", flush=True)

def scan_repo(repo, scanned_set):
    """单个仓库的扫描逻辑，供线程池调用"""
    homepage = repo.get("homepage")
    if not homepage or not homepage.startswith("http"): return None
    
    domain = urlparse(homepage).netloc
    if not domain or domain in scanned_set: return None
    
    extractor = ConfigExtractor()
    targets = [homepage.rstrip("/"), f"{homepage.rstrip('/')}/docs", f"https://docs.{domain}"]
    targets = list(dict.fromkeys(targets))
    
    found_url = None
    for url in targets:
        if extractor.scan(url):
            found_url = url
            break
    
    if found_url:
        print(f"Checking {domain} ... 🔍 FOUND CONFIG! Verifying...", flush=True)
        if verify_site_chat(found_url):
            print(f"   {domain} ✅ VERIFIED", flush=True)
            alias = repo['name'].lower().replace('.', '-').replace('_', '-')
            desc = (repo.get('description') or f"Docs for {repo['name']}")[:60].replace('"', '\\"').replace('\n', ' ')
            return {"alias": alias, "url": found_url, "desc": desc, "domain": domain}
        else:
            print(f"   {domain} ⚠️ Verification Failed", flush=True)
    else:
        # 即使没找到，也记录域名已扫描
        pass
        
    return {"domain": domain, "found": False}

def main():
    if not GITHUB_TOKEN: print("❌ GITHUB_TOKEN not set"); sys.exit(1)
    
    start_time = time.time()
    state = load_state()
    scanned = set(state["scanned_domains"])
    
    print(f"🚀 Starting Miner (Max {MAX_RUNTIME_SECONDS}s, Concurrency 10)...", flush=True)
    total_new = 0
    
    while True:
        if time.time() - start_time > MAX_RUNTIME_SECONDS:
            print("⏰ Time limit reached.", flush=True); break
            
        repos, next_max, next_grad = search_github(state)
        state["max_stars"] = next_max
        state["last_gradient"] = next_grad
        
        if not repos:
            if state["max_stars"] < 50: 
                state["max_stars"] = 500000
                break
            continue

        batch_new = 0
        # 使用线程池并发扫描网站
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_repo = {executor.submit(scan_repo, repo, scanned): repo for repo in repos}
            
            for future in as_completed(future_to_repo):
                result = future.result()
                if result:
                    scanned.add(result["domain"])
                    if "alias" in result:
                        update_registry_file(result)
                        batch_new += 1
                        total_new += 1
                        state["found_sites"].append(result["url"])

        state["scanned_domains"] = list(scanned)
        save_state(state)
        if batch_new > 0: update_readmes()
        
        if time.time() - start_time > MAX_RUNTIME_SECONDS: break

    print(f"\n🏁 Finished. Total new sites: {total_new}", flush=True)

if __name__ == "__main__":
    main()