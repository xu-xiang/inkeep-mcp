import * as cheerio from 'cheerio';

export interface InkeepConfig {
  apiKey?: string;
  integrationId?: string;
  [key: string]: any;
}

const USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

export async function extractConfig(url: string): Promise<InkeepConfig | null> {
  try {
    const res = await fetch(url, { headers: { "User-Agent": USER_AGENT } });
    if (!res.ok) return null;
    const html = await res.text();
    const $ = cheerio.load(html);
    const scripts = $('script');
    
    for (const script of scripts) {
      const content = $(script).html() || "";
      if (content.includes("integrationId") || content.includes("apiKey")) {
        const idMatch = /['"]integrationId['"]\s*:\s*['"]([a-zA-Z0-9-]+)['"]/.exec(content);
        const keyMatch = /['"]apiKey['"]\s*:\s*['"]([a-zA-Z0-9-]+)['"]/.exec(content);
        if (idMatch || keyMatch) {
          return { integrationId: idMatch?.[1], apiKey: keyMatch?.[1] };
        }
      }
    }
    return null;
  } catch (e) { return null; }
}
