import requests
import uuid
import json
from urllib.parse import urlparse
from .cache import CacheManager
from .extractor import ConfigExtractor
from .pow import PoWSolver

class InkeepClient:
    def __init__(self, target_url, cache_dir=None):
        self.target_url = target_url
        self.domain = urlparse(target_url).netloc
        self.base_url = f"https://{self.domain}"
        
        self.session = requests.Session()
        self.headers = {
            "origin": self.base_url,
            "referer": self.target_url,
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        }
        
        self.cache = CacheManager(cache_dir)
        self.extractor = ConfigExtractor(self.session)
        self.config = None

    def initialize(self, force_refresh=False):
        """Loads config from cache or scans the site."""
        if not force_refresh:
            cached = self.cache.get_config(self.target_url)
            if cached:
                self.config = cached['config']
                return True
        
        # Cache miss or forced refresh: scan
        config = self.extractor.scan(self.target_url)
        if config:
            self.config = config
            self.cache.set_config(self.target_url, config)
            return True
        
        return False

    def ask(self, question, stream=True):
        """
        Executes the query. Handles auto-retry on 401 Unauthorized.
        """
        # First attempt
        try:
            for chunk in self._ask_internal(question):
                yield chunk
        except PermissionError:
            # 401 detected in _ask_internal
            # yield "[System] Session expired. Refreshing keys..." # Optional: inform user
            
            # Clear cache and force re-initialization
            self.cache.clear_config(self.target_url)
            if self.initialize(force_refresh=True):
                try:
                    # Retry once
                    for chunk in self._ask_internal(question):
                        yield chunk
                except Exception as e:
                    yield f"[Error] Retry failed: {e}"
            else:
                yield "[Error] Failed to refresh configuration."

    def _ask_internal(self, question):
        if not self.config:
            if not self.initialize():
                yield "[Error] Could not initialize client (Config not found)"
                return

        # 1. Challenge
        try:
            challenge_res = self.session.get(
                "https://api.inkeep.com/v1/challenge",
                headers=self.headers,
                timeout=10
            )
            if challenge_res.status_code != 200:
                yield f"[Error] Challenge failed: {challenge_res.status_code}"
                return
            
            solution = PoWSolver.solve(challenge_res.json())
        except Exception as e:
            yield f"[Error] PoW failed: {e}"
            return

        # 2. Chat
        url = "https://api.inkeep.com/v1/chat/completions"
        chat_headers = self.headers.copy()
        
        if 'apiKey' in self.config:
            chat_headers["authorization"] = f"Bearer {self.config['apiKey']}"
        elif 'integrationId' in self.config:
             chat_headers["authorization"] = f"Bearer {self.config['integrationId']}"

        chat_headers.update({
            "accept": "application/json",
            "content-type": "application/json",
            "x-inkeep-challenge-solution": solution,
            "x-stainless-helper-method": "stream"
        })

        payload = {
            "model": "inkeep-qa-expert",
            "messages": [{"role": "user", "content": question, "id": str(uuid.uuid4())}],
            "stream": True
        }

        try:
            res = self.session.post(url, headers=chat_headers, json=payload, stream=True)
            
            if res.status_code == 401:
                # Signal caller to retry
                raise PermissionError("401 Unauthorized")
            
            if res.status_code != 200:
                yield f"[Error] API Error {res.status_code}: {res.text}"
                return

            for line in res.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: "):
                        data_str = decoded[6:].strip()
                        if data_str == "[DONE]": break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data:
                                content = data["choices"][0]["delta"].get("content", "")
                                if content: yield content
                        except: continue
        except PermissionError:
            raise
        except Exception as e:
            yield f"[Error] Request failed: {e}"