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

GITHUB_TOKEN = os.environ.get("MINER_TOKEN") or os.environ.get("GITHUB_TOKEN")
STATE_FILE = Path("github_miner/state.json")

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
    remaining = int(res.headers.get("x-ratelimit-remaining", 10))
    limit = int(res.headers.get("x-ratelimit-limit", 30))
    reset_time = int(res.headers.get("x-ratelimit-reset", time.time() + 60))
    buffer = max(3, int(limit * 0.1))
    if remaining <= buffer:
        sleep_seconds = reset_time - time.time() + 5
        print(f"⚠️ Rate limit low ({remaining}/{limit}). Sleeping for {sleep_seconds:.0f}s...")
        time.sleep(max(5, sleep_seconds))

def search_github(max_stars):
    if max_stars < 50:
        print("Stars limit reached. Resetting to top.")
        return [], 500000 

    query = f"stars:1..{max_stars} homepage:http* archived:false fork:false"
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 100, "page": 1}
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {GITHUB_TOKEN}"}

    print(f"🔍 Searching GitHub: stars <= {max_stars} ...")
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code in [403, 429]:
            check_rate_limit(res)
            return search_github(max_stars)
        if res.status_code != 200:
            print(f"❌ API Error {res.status_code}")
            return [], max_stars
        check_rate_limit(res)
        items = res.json().get("items", [])
        if not items: return [], 50
        min_stars = items[-1]["stargazers_count"]
        return items, (min_stars - 1 if min_stars == max_stars else min_stars)
    except Exception as e:
        print(f"❌ Exception: {e}")
        return [], max_stars

def update_registry_file(new_site):
    file_path = Path("inkeep_core/registry.py")
    with open(file_path, 'r') as f:
        content = f.read()
    
    alias, url, desc = new_site['alias'], new_site['url'], new_site['desc']
    if f'"{alias}"' in content:
        return

    entry = f'''    "{alias}": {{
        "url": "{url}",
        "description": "{desc}"
    }}'''

    # 精准匹配 # END_DEFAULT_SITES 之前的最后一个条目
    # 我们要在最后一个 } 后面补逗号，然后插入新条目
    pattern = r'(\s+)(\