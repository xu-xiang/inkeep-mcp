import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# 将项目根目录加入路径，以便导入 inkeep_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inkeep_core.extractor import ConfigExtractor
from inkeep_core.registry import SiteRegistry

def check_site(url):
    """检测单个站点是否接入 Inkeep"""
    extractor = ConfigExtractor()
    # 尝试根目录和 /docs
    paths = ["", "/docs", "/introduction", "/home"]
    
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme else f"https://{url.strip('/')}"
    
    for path in paths:
        target = base + path
        # print(f"  [Checking] {target}")
        config = extractor.scan(target)
        if config:
            return {"url": url, "detected_url": target, "found": True, "config": config}
            
    return {"url": url, "found": False}

def main():
    parser = argparse.ArgumentParser(description="Batch Inkeep Detector")
    parser.add_argument("input", help="File with list of URLs/domains")
    parser.add_argument("--output", default="scanner/scan_results.json", help="Output JSON file")
    parser.add_argument("--threads", type=int, default=10, help="Max threads")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File {args.input} not found")
        return

    with open(args.input, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"🚀 Starting scan for {len(urls)} sites using {args.threads} threads...")
    
    results = []
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        future_to_url = {executor.submit(check_site, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                res = future.result()
                if res['found']:
                    print(f"✅ FOUND: {url} -> {res['detected_url']}")
                    results.append(res)
                else:
                    print(f"⚪ Not found: {url}")
            except Exception as exc:
                print(f"❌ Error scanning {url}: {exc}")

    # 保存结果
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\n📊 Scan finished. Found {len(results)} Inkeep sites.")
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
