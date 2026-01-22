import hashlib
import json
import base64

class PoWSolver:
    @staticmethod
    def solve(challenge_data):
        """
        Solves the Inkeep Altcha PoW challenge.
        Algorithm: SHA-256(salt + str(number)) == challenge
        """
        challenge = challenge_data.get('challenge')
        salt = challenge_data.get('salt')
        max_number = challenge_data.get('maxnumber', 100000)
        signature = challenge_data.get('signature')

        if not challenge or not salt or not signature:
            raise ValueError("Invalid challenge data")

        for i in range(max_number + 1):
            h = hashlib.sha256((salt + str(i)).encode()).hexdigest()
            if h == challenge:
                solution = {
                    "number": i,
                    "algorithm": "SHA-256",
                    "challenge": challenge,
                    "maxnumber": max_number,
                    "salt": salt,
                    "signature": signature
                }
                return base64.b64encode(json.dumps(solution).encode()).decode()
        
        raise Exception(f"Failed to solve PoW challenge within max_number={max_number}")
