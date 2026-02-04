import { extractConfig, InkeepConfig } from './extractor';
import { solveChallenge } from './pow';
import { createParser } from 'eventsource-parser';

export async function* askInkeep(url: string, message: string) {
  // 1. Get Config
  yield { type: 'status', content: `Scanning ${url} for configuration...` };
  const config = await extractConfig(url);
  
  if (!config) {
    yield { type: 'error', content: 'Failed to extract Inkeep configuration from target site.' };
    return;
  }
  
  // 2. Get Challenge
  yield { type: 'status', content: 'Requesting PoW challenge...' };
  const headers = {
    "Origin": new URL(url).origin,
    "Referer": url,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json"
  };

  const challengeRes = await fetch("https://api.inkeep.com/v1/challenge", { headers });
  if (!challengeRes.ok) {
    yield { type: 'error', content: `Challenge failed: ${challengeRes.status}` };
    return;
  }
  
  // 3. Solve Challenge
  yield { type: 'status', content: 'Solving SHA-256 PoW challenge (Edge Compute)...' };
  const challengeData = await challengeRes.json();
  const solution = await solveChallenge(challengeData);

  // 4. Send Chat Request
  const chatUrl = "https://api.inkeep.com/v1/chat/completions";
  const chatHeaders: any = { ...headers, "x-inkeep-challenge-solution": solution };
  
  if (config.apiKey) chatHeaders["Authorization"] = `Bearer ${config.apiKey}`;
  else if (config.integrationId) chatHeaders["Authorization"] = `Bearer ${config.integrationId}`;

  const payload = {
    model: "inkeep-qa-expert",
    messages: [{ role: "user", content: message }],
    stream: true
  };

  const response = await fetch(chatUrl, {
    method: "POST",
    headers: chatHeaders,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    yield { type: 'error', content: `API Error: ${response.status} ${response.statusText}` };
    return;
  }

  // 5. Parse SSE Stream
  const reader = response.body?.getReader();
  if (!reader) return;

  const parser = createParser((event) => {
    if (event.type === 'event') {
      if (event.data === '[DONE]') return;
      try {
        const json = JSON.parse(event.data);
        const content = json.choices?.[0]?.delta?.content || "";
        if (content) {
          // Ideally we yield here, but generator inside callback is tricky.
          // We'll handle this by pushing to a buffer or using a specialized async iterator.
          // For simplicity in this Edge function context, let's use a simpler approach below.
        }
      } catch (e) {}
    }
  });
  
  // Simplified SSE parsing manually for generator compatibility
  const decoder = new TextDecoder();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      const lines = chunk.split('
');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data === '[DONE]') break;
          try {
            const json = JSON.parse(data);
            const content = json.choices?.[0]?.delta?.content;
            if (content) yield { type: 'delta', content };
          } catch (e) {}
        }
      }
    }
  } catch (e) {
    yield { type: 'error', content: `Stream error: ${e}` };
  }
}
