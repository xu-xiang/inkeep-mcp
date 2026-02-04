export interface ChallengeData {
  algorithm: string;
  challenge: string;
  maxnumber: number;
  salt: string;
  signature: string;
}

export interface Solution {
  number: number;
  algorithm: string;
  challenge: string;
  maxnumber: number;
  salt: string;
  signature: string;
}

export async function solveChallenge(challengeData: ChallengeData): Promise<string> {
  const { challenge, salt, maxnumber } = challengeData;
  const encoder = new TextEncoder();
  
  // Brute force from 0 to maxnumber
  for (let i = 0; i <= maxnumber; i++) {
    const candidate = i.toString();
    const data = encoder.encode(salt + candidate);
    
    // Calculate SHA-256
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    
    // Convert to hex string
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    if (hashHex === challenge) {
      // Found it! Construct solution JSON
      const solution: Solution = {
        number: i,
        algorithm: "SHA-256",
        challenge: challenge,
        maxnumber: maxnumber,
        salt: salt,
        signature: challengeData.signature
      };
      
      // Return Base64 encoded JSON string
      const jsonStr = JSON.stringify(solution);
      return btoa(jsonStr);
    }
  }
  
  throw new Error(`Failed to solve PoW challenge within max_number=${maxnumber}`);
}