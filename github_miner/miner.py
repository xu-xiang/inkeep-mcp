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

# Max runtime per execution (GitHub Action standard timeout is 6h, but we schedule hourly)
# We stop at 45 minutes to allow plenty of time for commit/push and overhead.
MAX_RUNTIME_SECONDS = 45 * 60 

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            if "max_stars" not in state: state["max_stars"] = 500000
            if "scanned_domains" not in state: state["scanned_domains"] = []
            return state
    return {"max_stars": 500000, "scanned_domains": [], "found_sites": []}

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

def search_github(max_stars):
    if max_stars < 10:
        print("Stars floor reached.")
        return [], 500000
    query = f"stars:<={max_stars} archived:false fork:false"
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 100, "page": 1}
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {GITHUB_TOKEN}"}
    print(f"🔍 Searching: stars <= {max_stars} ...")
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code in [403, 429]:
            check_rate_limit(res); return search_github(max_stars)
        if res.status_code != 200:
            print(f"❌ API Error {res.status_code}"); return [], max_stars
        check_rate_limit(res)
        items = res.json().get("items", [])
        if not items: return [], 50 
        first, last = items[0]["stargazers_count"], items[-1]["stargazers_count"]
        print(f"   Batch: Top={first}, Bottom={last}, Count={len(items)}")
        next_max = last
        if len(items) >= 100 and next_max == max_stars: next_max -= 1
        return items, next_max
    except Exception as e:
        print(f"❌ Exception: {e}"); return [], max_stars

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
    
    print(f"🚀 Starting continuous mining session (Max {MAX_RUNTIME_SECONDS}s)...")
    
    total_findings = 0
    
    while True:
        # Time check
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print(f"⏰ Time limit reached ({elapsed:.0f}s). Stopping gracefully.")
            break
            
        repos, next_max_stars = search_github(state["max_stars"])
        
        # If no items or we hit the floor, reset loop (but maybe stop to avoid API burn)
        if not repos or next_max_stars >= state["max_stars"]:
             # If we didn't progress, stop to prevent infinite loop spamming API
             if state["max_stars"] < 50:
                 state["max_stars"] = 500000 # Reset for next hour
             print("End of search cycle reached.")
             break

        batch_findings = 0
        for repo in repos:
            # Check time even inside the inner loop for fine-grained control
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
                    batch_findings += 1
                    total_findings += 1
                    state["found_sites"].append(found_url)
                else: print("⚠️ Verification Failed")
            else: print("⚪")
            scanned.add(domain)
        
        # Save state immediately after each batch
        state["max_stars"] = next_max_stars
        state["scanned_domains"] = list(scanned)
        save_state(state)
        
        if batch_findings > 0:
            update_readmes()
            
    print(f"\n🏁 Session Complete. Total new sites found this run: {total_findings}")

if __name__ == "__main__":
    main()