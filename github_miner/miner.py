import os
import sys
import json
import time
import requests
import re
from urllib.parse import urlparse
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inkeep_core.extractor import ConfigExtractor
from inkeep_core.registry import SiteRegistry
from inkeep_core.client import InkeepClient

GITHUB_TOKEN = os.environ.get("MINER_TOKEN") or os.environ.get("GITHUB_TOKEN")
STATE_FILE = Path("github_miner/state.json")

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            # 增加 last_gradient 字段，默认为 1000
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
            print(f"⚠️ Rate limit low ({remaining}/{limit}). Sleeping for {sleep_seconds:.0f}s...")
            if sleep_seconds > 0: time.sleep(sleep_seconds)
    except: pass

def search_github(state):
    """
    Executes search with Dynamic Gradient logic.
    Returns: (repos, next_max_stars, next_gradient)
    """
    max_stars = state["max_stars"]
    gradient = state.get("last_gradient", 1000)
    
    if max_stars < 10:
        print("Stars floor reached.")
        return [], 500000, 1000

    # --- 1. Bootstrapping Logic (First 2 runs hardcoded) ---
    # Fix: Use correct range syntax stars:MIN..MAX
    if max_stars == 500000:
        query = "stars:24000..500000 pushed:>=2025-11-04 fork:false archived:false"
        print(f"🔍 [Bootstrap 1] Query: {query}")
    elif max_stars == 24000:
        query = "stars:23000..24000 pushed:>=2025-11-04 fork:false archived:false"
        print(f"🔍 [Bootstrap 2] Query: {query}")
    else:
        # --- 2. Dynamic Gradient Logic ---
        min_stars = max(0, max_stars - gradient)
        query = f"stars:{min_stars}..{max_stars} archived:false fork:false"
        print(f"🔍 [Dynamic] Query: {query} (Gradient: {gradient})")

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 100, "page": 1}
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {GITHUB_TOKEN}"}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        
        # Critical: Handle 422 (Invalid Query) - Do not retry
        if res.status_code == 422:
            print(f"❌ API Error 422: Invalid Query. {res.text}")
            # Skip this range to avoid infinite loop
            return [], max_stars - gradient, gradient

        if res.status_code in [403, 429]:
            print(f"⚠️ Rate limit hit (Status {res.status_code})")
            check_rate_limit(res)
            return search_github(state) # Retry
            
        if res.status_code != 200:
            print(f"❌ API Error {res.status_code}: {res.text}")
            return [], max_stars, gradient

        check_rate_limit(res)
        
        items = res.json().get("items", [])
        
        if not items:
            print(f"   No items in range. Increasing gradient.")
            # Nothing found? Increase gradient to search wider next time
            new_gradient = gradient * 2
            return [], max_stars - gradient, new_gradient
            
        first = items[0]["stargazers_count"]
        last = items[-1]["stargazers_count"]
        count = len(items)
        print(f"   Result: Count={count}, Top={first}, Bottom={last}")
        
        # --- 3. Calculate Next State ---
        next_max = last
        if next_max == max_stars: 
            next_max -= 1
            
        # Calculate Next Gradient
        if count < 100:
            next_gradient = int(gradient * 1.5)
            print(f"   -> Sparse batch (<100). Increasing gradient to {next_gradient}")
        else:
            actual_spread = first - last
            next_gradient = max(100, actual_spread)
            print(f"   -> Full batch. Adjusting gradient to actual spread: {next_gradient}")

        return items, next_max, next_gradient

    except Exception as e:
        print(f"❌ Exception: {e}")
        return [], max_stars, gradient

def verify_site_chat(url):
    print(f"   Verifying chat for {url} ...", end="", flush=True)
    try:
        client = InkeepClient(url)
        for chunk in client.ask("Hello"):
            if "[Error]" in chunk:
                print(f" ❌ Failed: {chunk}"); return False
            print(" ✅ OK"); return True
    except Exception as e:
        print(f" ❌ Exception: {e}"); return False
    return False

def update_registry_file(new_site):
    file_path = Path("inkeep_core/registry.py")
    with open(file_path, 'r') as f: content = f.read()
    alias, url, desc = new_site['alias'], new_site['url'], new_site['desc']
    if f'"{alias}"' in content: return
    tag = "} # END_DEFAULT_SITES"
    tag_index = content.find(tag)
    if tag_index != -1:
        prefix = content[:tag_index].rstrip()
        suffix = content[tag_index:]
        if not prefix.endswith(","): prefix += ","
        entry = f'\n    \"{alias}\": {{ \n        \"url\": \"{url}\",\n        \"description\": \"{desc}\"\n    }}'
        with open(file_path, 'w') as f: f.write(prefix + entry + "\n" + suffix)
        print(f"🎉 Code Updated: Added {alias}")

def update_readmes():
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
            if is_zh and desc.startswith("Docs for "):
                desc = desc.replace("Docs for ", "") + " 官方文档"
            elif is_zh and desc.startswith("Official docs for "):
                desc = desc.replace("Official docs for ", "") + " 官方文档"
            md_lines.append(f"*   **{name}** ({desc})")
        md_content = "\n".join(md_lines)
        with open(readme_file, 'r') as f: text = f.read()
        pattern = r"(<!-- AUTO-GENERATED-SITES:START -->)(.*?)(<!-- AUTO-GENERATED-SITES:END -->)"
        replacement = f"\1\n{md_content}\n\3"
        new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)
        with open(readme_file, 'w') as f: f.write(new_text)
        print(f"📝 Updated {readme_file}")

def main():
    if not GITHUB_TOKEN: print("❌ GITHUB_TOKEN not set"); sys.exit(1)
    
    start_time = time.time()
    state = load_state()
    scanned = set(state["scanned_domains"])
    extractor = ConfigExtractor()
    
    MAX_RUNTIME_SECONDS = 45 * 60 
    
    print(f"🚀 Starting continuous mining session (Max {MAX_RUNTIME_SECONDS}s)...")
    
    total_findings = 0
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print(f"⏰ Time limit reached. Stopping.")
            break
            
        repos, next_max, next_grad = search_github(state)
        
        # Update logic state immediately
        state["max_stars"] = next_max
        state["last_gradient"] = next_grad
        
        if not repos:
             if state["max_stars"] < 50:
                 state["max_stars"] = 500000 
                 print("Resetting to top.")
             else:
                 pass
        
        batch_findings = 0
        for repo in repos:
            if time.time() - start_time > MAX_RUNTIME_SECONDS: break
            
            homepage = repo.get("homepage")
            if not homepage or not homepage.startswith("http"): continue
            domain = urlparse(homepage).netloc
            if not domain or domain in scanned: continue
            
            print(f"Checking {domain} ...", end=" ")
            targets = [homepage.rstrip("/"), f"{homepage.rstrip('/')}/docs", f"https://docs.{domain}"]
            targets = list(dict.fromkeys(targets))
            
            found_url = None
            for url in targets:
                if extractor.scan(url): found_url = url; break
            
            if found_url:
                print(f"🔍 FOUND CONFIG! Now verifying...")
                if verify_site_chat(found_url):
                    alias = repo['name'].lower().replace('.', '-').replace('_', '-')
                    desc = (repo.get('description') or f"Docs for {repo['name']}")[:60].replace('"', '\\"').replace('\n', ' ')
                    update_registry_file({"alias": alias, "url": found_url, "desc": desc})
                    batch_findings += 1; total_findings += 1; state["found_sites"].append(found_url)
                else: print("⚠️ Verification Failed")
            else: print("⚪")
            scanned.add(domain)
        
        state["scanned_domains"] = list(scanned)
        save_state(state)
        
        if batch_findings > 0: update_readmes()
            
    print(f"\n🏁 Session Complete. New sites: {total_findings}")

if __name__ == "__main__":
    main()