import os
import sys
import json
import time
import requests
import re
from urllib.parse import urlparse
from pathlib import Path

# Add project root to sys.path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inkeep_core.extractor import ConfigExtractor
from inkeep_core.registry import SiteRegistry

GITHUB_TOKEN = os.environ.get("MINER_TOKEN") or os.environ.get("GITHUB_TOKEN")
STATE_FILE = Path("github_miner/state.json")
REGISTRY_FILE = Path("inkeep_core/registry.py")

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            if "scanned_domains" not in state: state["scanned_domains"] = []
            if "max_stars" not in state: state["max_stars"] = 500000
            return state
    return {"max_stars": 500000, "scanned_domains": [], "found_sites": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_rate_limit(res):
    """
    Proactively sleep if rate limit is running low (leave 10% buffer).
    Search API limit is usually 30/min. Buffer = 3.
    """
    remaining = int(res.headers.get("x-ratelimit-remaining", 10))
    limit = int(res.headers.get("x-ratelimit-limit", 30))
    reset_time = int(res.headers.get("x-ratelimit-reset", time.time() + 60))
    
    # 10% buffer
    buffer = max(3, int(limit * 0.1))
    
    if remaining <= buffer:
        sleep_seconds = reset_time - time.time() + 5
        print(f"⚠️ Rate limit low ({remaining}/{limit}). Sleeping for {sleep_seconds:.0f}s...")
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

def search_github(max_stars):
    """
    Search repos with stars <= max_stars.
    Returns: (repos, min_stars_in_batch)
    """
    if max_stars < 50:
        print("Stars limit reached. Resetting to top.")
        return [], 500000 

    query = f"stars:1..{max_stars} homepage:http* archived:false fork:false"
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

    print(f"🔍 Searching GitHub: stars <= {max_stars} ...")
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        
        # 1. Handle hard limit hit
        if res.status_code == 403 or res.status_code == 429:
            print(f"⚠️ Rate limit hit (403/429).")
            check_rate_limit(res)
            return search_github(max_stars) # Retry
            
        if res.status_code != 200:
            print(f"❌ API Error {res.status_code}: {res.text}")
            return [], max_stars

        # 2. Proactive check for next request
        check_rate_limit(res)

        data = res.json()
        items = data.get("items", [])
        
        if not items:
            print("No more items found in this range.")
            return [], 50 # Done
            
        min_stars_found = items[-1]["stargazers_count"]
        if min_stars_found == max_stars:
            min_stars_found -= 1
            
        print(f"✅ Got {len(items)} repos. New star ceiling: {min_stars_found}")
        return items, min_stars_found

    except Exception as e:
        print(f"❌ Exception: {e}")
        return [], max_stars

def update_registry_file(new_site):
    """
    Directly modifies inkeep_core/registry.py to insert the new site.
    This is hacky but effective for self-evolving code.
    """
    file_path = Path("inkeep_core/registry.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    alias = new_site['alias']
    url = new_site['url']
    desc = new_site['desc']
    
    # Check if already exists in text
    if f'"{alias}"' in content:
        print(f"⚠️ {alias} already in registry.py")
        return

    # Insert before the closing brace of DEFAULT_SITES
    
    entry_template = f'''    "{alias}": {{
        "url": "{url}",
        "description": "{desc}"
    }},
'''
    # Regex to find the last dictionary entry before the closing brace
    # Matches: 4 spaces, quoted key, colon, brace block, optional comma/newline, then capturing group for the closing brace
    pattern = r'(    "[^"]+": \{[^}]+\}[,]*\n)(\})'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # Insert before the last closing brace
        last_entry = match.group(1)
        # Ensure last entry has a comma
        if not last_entry.strip().endswith(","):
            last_entry = last_entry.rstrip() + ",\n"
            
        new_content = content[:match.start(1)] + last_entry + entry_template + "}" + content[match.end(2):]
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"🎉 Code Updated: Added {alias} to registry.py")
    else:
        print("❌ Failed to patch registry.py: Pattern not found")

def main():
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set")
        sys.exit(1)

    state = load_state()
    scanned = set(state["scanned_domains"])
    
    # 1. Search
    repos, next_max_stars = search_github(state["max_stars"])
    
    # 2. Filter & Scan
    extractor = ConfigExtractor()
    new_findings = 0
    
    for repo in repos:
        homepage = repo.get("homepage")
        if not homepage: continue
        
        # Clean URL
        if not homepage.startswith("http"):
            homepage = f"https://{homepage}"
            
        domain = urlparse(homepage).netloc
        if not domain or domain in scanned:
            continue
            
        scanned.add(domain)
        
        # Try scanning doc paths
        targets = [
            homepage.rstrip("/"),
            f"{homepage.rstrip('/')}/docs",
            f"https://docs.{domain}"
        ]
        # Dedup targets
        targets = list(set(targets))
        
        print(f"Scanning {domain} ...", end=" ")
        
        found_config = None
        found_url = None
        
        for url in targets:
            # print(f"  Trying {url}...", end="")
            config = extractor.scan(url) # This prints its own logs
            if config:
                found_config = config
                found_url = url
                break
        
        if found_config:
            print(f"\n🚀 FOUND INKEEP! {domain}")
            
            # Prepare metadata
            alias = repo['name'].lower().replace('.', '-').replace('_', '-')
            desc = repo.get('description') or f"Official docs for {repo['name']}"
            desc = desc.replace('"', '\"').replace('\n', ' ') # Escape quotes and newlines
            desc = desc[:60] + "..." if len(desc) > 60 else desc # Truncate
            
            new_site = {
                "alias": alias,
                "url": found_url,
                "desc": desc
            }
            
            # Update Code
            update_registry_file(new_site)
            
            state["found_sites"].append(found_url)
            new_findings += 1
        else:
            print(" -> Nope.")

    # 3. Save State
    state["max_stars"] = next_max_stars
    state["scanned_domains"] = list(scanned)
    save_state(state)
    
    print(f"\n🏁 Batch Complete. Found {new_findings} new sites. Next star ceiling: {next_max_stars}")

if __name__ == "__main__":
    main()