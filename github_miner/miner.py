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
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
    except:
        pass

def search_github(max_stars):
    if max_stars < 10:
        print("Stars floor reached.")
        return [], 500000

    query = f"stars:<={max_stars} archived:false fork:false"
    url = "https://api.github.com/search/repositories"
    
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 100, 
        "page": 1
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    print(f"🔍 Searching: stars <= {max_stars} ...")
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        
        if res.status_code in [403, 429]:
            print(f"⚠️ Rate limit hit (Status {res.status_code})")
            check_rate_limit(res)
            return search_github(max_stars) # Retry
            
        if res.status_code != 200:
            print(f"❌ API Error {res.status_code}: {res.text}")
            return [], max_stars

        check_rate_limit(res)
        
        items = res.json().get("items", [])
        if not items:
            print("No items found.")
            return [], 50 
            
        first = items[0]["stargazers_count"]
        last = items[-1]["stargazers_count"]
        print(f"   Batch: Top={first}, Bottom={last}, Count={len(items)}")
        
        next_max = last
        if len(items) >= 100 and next_max == max_stars:
            next_max -= 1
            
        return items, next_max

    except Exception as e:
        print(f"❌ Exception: {e}")
        return [], max_stars

def verify_site_chat(url):
    """
    Verifies if the site actually works by sending a test chat message.
    """
    print(f"   Verifying chat for {url} ...", end="", flush=True)
    try:
        client = InkeepClient(url)
        # Try a simple greeting
        for chunk in client.ask("Hello"):
            # If we get any chunk, it's working (even if it's an error message from LLM, at least connection is OK)
            # But we want to filter out 403/401 errors which client.ask yields as strings starting with [Error]
            if "[Error]" in chunk:
                print(f" ❌ Failed: {chunk}")
                return False
            print(" ✅ OK")
            return True
    except Exception as e:
        print(f" ❌ Exception: {e}")
        return False
    return False

def update_registry_file(new_site):
    file_path = Path("inkeep_core/registry.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    alias, url, desc = new_site['alias'], new_site['url'], new_site['desc']
    if f'"{alias}"' in content:
        return

    tag = "} # END_DEFAULT_SITES"
    tag_index = content.find(tag)
    
    if tag_index != -1:
        prefix = content[:tag_index].rstrip()
        suffix = content[tag_index:]
        
        if not prefix.endswith(","):
            prefix += ","
            
        entry = f'''
    "{alias}": {{
        "url": "{url}",
        "description": "{desc}"
    }}'''
        
        with open(file_path, 'w') as f:
            f.write(prefix + entry + "\n" + suffix)
        print(f"🎉 Code Updated: Added {alias}")
    else:
        print("❌ Failed to patch registry.py - Tag not found")

def update_readmes():
    """
    Updates README.md and README_zh.md with the latest site list.
    """
    # Load current registry (from the file we just patched)
    # We re-import to get fresh data? No, we parse the file again or use regex?
    # Simpler: regex parse the file we just wrote to.
    
    file_path = Path("inkeep_core/registry.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract entries from DEFAULT_SITES block
    # This is a simple regex to grab keys and descriptions
    # Matches: "key": { ... "description": "desc" ... }
    # This is rough but should work for the standard format we write.
    
    # Better approach: Instantiate SiteRegistry? 
    # But SiteRegistry loads from ~/.inkeep/registry.json which is not updated yet.
    # It updates from DEFAULT_SITES on init. So if we just modified registry.py, we can import it?
    # Python caches imports. We need to reload.
    
    import importlib
    import inkeep_core.registry
    importlib.reload(inkeep_core.registry)
    
    # Now getting the dict from the module variable directly
    sites = inkeep_core.registry.DEFAULT_SITES
    
    # Generate Markdown list
    md_lines = []
    for alias, info in sites.items():
        name = alias.capitalize()
        desc = info['description']
        md_lines.append(f"*   **{name}** ({desc})")
    
    md_content = "\n".join(md_lines)
    
    for readme_file in ["README.md", "README_zh.md"]:
        if not os.path.exists(readme_file): continue
        
        with open(readme_file, 'r') as f:
            text = f.read()
        
        pattern = r"(<!-- AUTO-GENERATED-SITES:START -->)(.*?)(<!-- AUTO-GENERATED-SITES:END -->)"
        replacement = f"\1\n{md_content}\n\3"
        
        new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)
        
        with open(readme_file, 'w') as f:
            f.write(new_text)
        print(f"📝 Updated {readme_file}")

def main():
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set"); sys.exit(1)

    state = load_state()
    scanned = set(state["scanned_domains"])
    
    repos, next_max_stars = search_github(state["max_stars"])
    extractor = ConfigExtractor()
    new_findings = 0
    
    for repo in repos:
        homepage = repo.get("homepage")
        if not homepage or not homepage.startswith("http"): 
            continue
            
        domain = urlparse(homepage).netloc
        if not domain or domain in scanned: continue
        
        print(f"Scanning {domain} ...", end=" ")
        
        targets = [homepage.rstrip("/"), f"{homepage.rstrip('/')}/docs", f"https://docs.{domain}"]
        targets = list(dict.fromkeys(targets))
        
        found_url = None
        for url in targets:
            # Silence logs
            res = extractor.scan(url)
            if res:
                found_url = url
                break
        
        if found_url:
            print(f"🔍 FOUND CONFIG! Now verifying...")
            
            # New Step: Verification
            if verify_site_chat(found_url):
                alias = repo['name'].lower().replace('.', '-').replace('_', '-')
                desc = (repo.get('description') or f"Docs for {repo['name']}")[:60].replace('"', '\"').replace('\n', ' ')
                
                update_registry_file({
                    "alias": alias,
                    "url": found_url,
                    "desc": desc
                })
                new_findings += 1
                state["found_sites"].append(found_url)
            else:
                print("⚠️ Verification Failed (Chat not working)")
        else:
            print("⚪")
        scanned.add(domain)

    state["max_stars"] = next_max_stars
    state["scanned_domains"] = list(scanned)
    save_state(state)
    
    if new_findings > 0:
        print(f"Updating READMEs with {new_findings} new sites...")
        update_readmes()
        
    print(f"\n🏁 Batch Complete. Found {new_findings} new sites. Next ceiling: {next_max_stars}")

if __name__ == "__main__":
    main()