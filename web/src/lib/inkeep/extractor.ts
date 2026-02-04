import * as cheerio from 'cheerio';

export interface InkeepConfig {
  apiKey?: string;
  integrationId?: string;
}

const USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

export async function extractConfig(url: string): Promise<InkeepConfig | null> {
  try {
    const res = await fetch(url, { headers: { "User-Agent": USER_AGENT } });
    if (!res.ok) return null;
    
    const html = await res.text();
    const $ = cheerio.load(html);
    const baseUrl = new URL(url).origin;
    
    // 1. Find all script tags with 'src'
    const scriptUrls: string[] = [];
    $('script[src]').each((_, el) => {
      const src = $(el).attr('src');
      if (src) {
        try {
          scriptUrls.push(new URL(src, baseUrl).href);
        } catch (e) {}
      }
    });

    // 2. Prioritize scripts that might contain Inkeep config
    const priority = scriptUrls.filter(u => /inkeep|app|main|page|_app|layout/i.test(u));
    const others = scriptUrls.filter(u => !/inkeep|app|main|page|_app|layout/i.test(u));
    const candidates = [...new Set([...priority, ...others])].slice(0, 30); // Max 30 scripts

    const patterns = [
      { regex: /apiKey\s*:\s*["']([a-f0-9]{32,})["']/, key: 'apiKey' },
      { regex: /integrationId\s*:\s*["']([a-zA-Z0-9_-]{20,})["']/, key: 'integrationId' }
    ];

    // 3. Scan scripts in parallel (with limit)
    const results = await Promise.all(
      candidates.map(async (jsUrl) => {
        try {
          const jsRes = await fetch(jsUrl, { 
            headers: { "User-Agent": USER_AGENT },
            signal: AbortSignal.timeout(5000) 
          });
          if (!jsRes.ok) return null;
          const content = await jsRes.text();
          
          for (const p of patterns) {
            const match = p.regex.exec(content);
            if (match) return { [p.key]: match[1] };
          }
          return null;
        } catch (e) { return null; }
      })
    );

    const found = results.find(r => r !== null);
    return found || null;

  } catch (e) {
    return null;
  }
}
