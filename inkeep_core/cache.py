import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

class CacheManager:
    def __init__(self, cache_dir=None):
        if cache_dir:
            self.cache_path = Path(cache_dir) / "cache.json"
        else:
            self.cache_path = Path.home() / ".inkeep" / "cache.json"
        
        self._ensure_cache_dir()
        self.cache = self._load_cache()

    def _ensure_cache_dir(self):
        if not self.cache_path.parent.exists():
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self):
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def get_domain(self, url):
        return urlparse(url).netloc

    def get_config(self, url):
        domain = self.get_domain(url)
        return self.cache.get(domain)

    def set_config(self, url, config):
        domain = self.get_domain(url)
        self.cache[domain] = {
            "config": config,
            "updated_at": time.time(),
            "url": url
        }
        self._save_cache()

    def clear_config(self, url):
        domain = self.get_domain(url)
        if domain in self.cache:
            del self.cache[domain]
            self._save_cache()
