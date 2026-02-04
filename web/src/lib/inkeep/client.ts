import { extractConfig } from './extractor';
import { solveChallenge } from './pow';

export async function* askInkeep(url: string, message: string) {
  yield { type: 'status', content: `Scanning ${new URL(url).hostname} for live keys...` };
  
  const config = await extractConfig(url);
  
  if (!config) {
    yield { type: 'error', content: 'Failed to extract Inkeep configuration. Please ensure the target site is supported.' };
    return;
  }
  
  const targetOrigin = new URL(url).origin;
  const commonHeaders = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": targetOrigin,
    "Referer": url,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site"
  };

  // 1. Get Challenge
  yield { type: 'status', content: 'Requesting secure session...' };
  const challengeRes = await fetch("https://api.inkeep.com/v1/challenge", { headers: commonHeaders });
  
  if (!challengeRes.ok) {
    yield { type: 'error', content: `Security Gate Error: ${challengeRes.status}` };
    return;
  }
  
  // 2. Solve Challenge
  yield { type: 'status', content: 'Solving PoW challenge...' };
  const challengeData = await challengeRes.json();
  const solution = await solveChallenge(challengeData);

  // 3. Chat
  const chatUrl = "https://api.inkeep.com/v1/chat/completions";
  // Important: apiKey and integrationId are used interchangeably as Bearer tokens
  const authHeader = `Bearer ${config.apiKey || config.integrationId}`;
  
  const chatHeaders = {
    ...commonHeaders,
    "Authorization": authHeader,
    "Content-Type": "application/json",
    "x-inkeep-challenge-solution": solution,
    "x-stainless-helper-method": "stream"
  };

  const payload = {
    model: "inkeep-qa-expert",
    messages: [{ role: "user", content: message }],
    stream: true
  };

  yield { type: 'status', content: 'Retrieving official answer...' };

  const response = await fetch(chatUrl, {
    method: "POST",
    headers: chatHeaders,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorBody = await response.text();
    yield { type: 'error', content: `Inkeep API Error (${response.status}): ${errorBody}` };
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;
        const data = trimmed.slice(6);
        if (data === '[DONE]') break;
        try {
          const json = JSON.parse(data);
          const content = json.choices?.[0]?.delta?.content;
          if (content) yield { type: 'delta', content };
        } catch (e) {}
      }
    }
  } catch (e) {
    yield { type: 'error', content: `Stream error: ${String(e)}` };
  }
}