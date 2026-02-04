import json
import os
from pathlib import Path

# 默认支持的黄金站点列表
DEFAULT_SITES = {
    "langfuse": {
        "url": "https://langfuse.com",
        "description": "Langfuse (LLM Engineering Platform) official documentation"
    },
    "render": {
        "url": "https://render.com/docs",
        "description": "Render (Cloud Hosting) official documentation"
    },
    "clerk": {
        "url": "https://clerk.com/docs",
        "description": "Clerk (Authentication) official documentation"
    },
    "neon": {
        "url": "https://neon.com/docs",
        "description": "Neon (Serverless Postgres) official documentation"
    },
    "teleport": {
        "url": "https://goteleport.com/docs",
        "description": "Teleport (Access Plane) official documentation"
    }
} # END_DEFAULT_SITES

class SiteRegistry:
    def __init__(self, config_dir=None):
        if config_dir:
            self.registry_path = Path(config_dir) / "registry.json"
        else:
            self.registry_path = Path.home() / ".inkeep" / "registry.json"
        
        self._ensure_dir()
        self.sites = self._load_registry()

    def _ensure_dir(self):
        if not self.registry_path.parent.exists():
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_registry(self):
        """
        加载注册表，并自动合并/更新内置的默认站点配置。
        这确保了当代码更新（如 Neon URL 变更）时，用户本地配置能自动修复。
        """
        if not self.registry_path.exists():
            self.save_registry(DEFAULT_SITES)
            return DEFAULT_SITES.copy()
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                
                # 智能合并：强制更新内置站点，保留用户自定义站点
                has_changes = False
                for alias, info in DEFAULT_SITES.items():
                    if alias not in data or data[alias] != info:
                        data[alias] = info
                        has_changes = True
                
                if has_changes:
                    self.save_registry(data)
                    
                return data
        except json.JSONDecodeError:
            self.save_registry(DEFAULT_SITES)
            return DEFAULT_SITES.copy()

    def save_registry(self, data=None):
        data = data if data is not None else self.sites
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_site(self, alias, url, description=None):
        if not description:
            description = f"Documentation for {alias}"
        
        self.sites[alias] = {
            "url": url,
            "description": description
        }
        self.save_registry()

    def remove_site(self, alias):
        if alias in self.sites:
            del self.sites[alias]
            self.save_registry()
            return True
        return False

    def get_url(self, alias_or_url):
        """
        智能解析输入：
        1. 检查是否为已注册的 alias。
        2. 检查是否为 URL (http/https)。
        3. 否则返回 None。
        """
        # Case 1: Alias match
        if alias_or_url in self.sites:
            return self.sites[alias_or_url]["url"]
        
        # Case 2: Direct URL
        if alias_or_url.startswith("http://") or alias_or_url.startswith("https://"):
            return alias_or_url
            
        return None

    def list_sites(self):
        return self.sites
