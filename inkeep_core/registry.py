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
    },
    "react": {
        "url": "https://react.dev",
        "description": "The library for web and native user interfaces."
    },
    "bootstrap": {
        "url": "https://getbootstrap.com",
        "description": "The most popular HTML, CSS, and JavaScript framework for dev"
    },
    "ragflow": {
        "url": "https://ragflow.io",
        "description": "RAGFlow is a leading open-source Retrieval-Augmented Generat"
    },
    "node": {
        "url": "https://base.org",
        "description": "Everything required to run your own Base node"
    },
    "socket-io": {
        "url": "https://socket.io",
        "description": "Realtime application framework (Node.JS server)"
    },
    "sway": {
        "url": "https://docs.fuel.network/docs/sway",
        "description": "🌴 Empowering everyone to build reliable and efficient smart "
    },
    "bun": {
        "url": "https://bun.com",
        "description": "Incredibly fast JavaScript runtime, bundler, test runner, and package manager."
    },
    "zod": {
        "url": "https://zod.dev",
        "description": "TypeScript-first schema validation with static type inference."
    },
    "novu": {
        "url": "https://docs.novu.co",
        "description": "The open-source notification Inbox infrastructure. E-mail, SMS, and Push."
    },
    "litellm": {
        "url": "https://docs.litellm.ai/docs",
        "description": "Python SDK, Proxy Server (AI Gateway) to call 100+ LLM APIs."
    },
    "posthog": {
        "url": "https://posthog.com",
        "description": "🦔 PostHog is an all-in-one developer platform for building products."
    },
    "goose": {
        "url": "https://block.github.io/goose",
        "description": "An open source, extensible AI agent that goes beyond code suggestions."
    },
    "frigate": {
        "url": "https://docs.frigate.video",
        "description": "NVR with realtime local object detection for IP cameras."
    },
    "fingerprintjs": {
        "url": "https://docs.fingerprint.com",
        "description": "The most advanced free and open-source browser fingerprinting."
    },
    "spacetimedb": {
        "url": "https://spacetimedb.com/docs",
        "description": "Multiplayer at the speed of light."
    },
    "nextra": {
        "url": "https://nextra.site",
        "description": "Simple, powerful and flexible site generation framework with Next.js."
    },
    "zitadel": {
        "url": "https://zitadel.com",
        "description": "ZITADEL - Identity infrastructure, simplified for you."
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
        if not self.registry_path.exists():
            self.save_registry(DEFAULT_SITES)
            return DEFAULT_SITES.copy()
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
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
        self.sites[alias] = { "url": url, "description": description }
        self.save_registry()

    def remove_site(self, alias):
        if alias in self.sites:
            del self.sites[alias]
            self.save_registry()
            return True
        return False

    def get_url(self, alias_or_url):
        if alias_or_url in self.sites:
            return self.sites[alias_or_url]["url"]
        if alias_or_url.startswith("http://") or alias_or_url.startswith("https://"):
            return alias_or_url
        return None

    def list_sites(self):
        return self.sites
