export interface ChallengeData {
  algorithm: string;
  challenge: string;
  maxnumber: number;
  salt: string;
  signature: string;
}

export async function solveChallenge(challengeData: ChallengeData): Promise<string> {
  const { challenge, salt, maxnumber, signature } = challengeData;
  const encoder = new TextEncoder();
  
  for (let i = 0; i <= maxnumber; i++) {
    const candidate = i.toString();
    const data = encoder.encode(salt + candidate);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    if (hashHex === challenge) {
      // 严格复刻 Python 的 JSON 序列化格式
      const jsonStr = `{"number": ${i}, "algorithm": "SHA-256", "challenge": "${challenge}", "maxnumber": ${maxnumber}, "salt": "${salt}", "signature": "${signature}"}`;
      
      // 在 Edge 环境中使用标准的 btoa
      return btoa(jsonStr);
    }
  }
  
  throw new Error(`Failed to solve PoW challenge within ${maxnumber}`);
}