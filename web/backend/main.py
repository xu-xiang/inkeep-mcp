import sys
import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Ensure we can import inkeep_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from inkeep_core.client import InkeepClient
    from inkeep_core.registry import SiteRegistry, DEFAULT_SITES
except ImportError as e:
    print(f"Error importing core modules: {e}")
    sys.exit(1)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    url: str

@app.get("/api/sites")
async def get_sites():
    """Returns the list of supported sites based on the core registry."""
    # Convert dictionary to a list of objects for easier frontend consumption
    sites = []
    for key, data in DEFAULT_SITES.items():
        sites.append({
            "id": key,
            "name": key.capitalize(), # Simple capitalization for display
            "url": data["url"],
            "description": data["description"]
        })
    return sites

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Real chat endpoint that uses InkeepClient to fetch answers.
    Returns a streaming response.
    """
    if not request.url:
        raise HTTPException(status_code=400, detail="Target URL is required")

    async def generate():
        try:
            # Initialize client for the specific target URL
            # Note: In a production server, we might want to cache clients or use a pool
            client = InkeepClient(request.url)
            
            # Send an initial "thinking" message
            yield json.dumps({"type": "status", "content": f"Connecting to {request.url}..."}) + "\n"
            await asyncio.sleep(0.5) # UI pacing
            
            yield json.dumps({"type": "status", "content": "Solving PoW challenge..."}) + "\n"
            
            # The client.ask is a generator (synchronous), so we iterate it
            # We wrap it in a thread executor if it blocks, but for now direct iteration
            # might block the event loop slightly. For a demo, it's acceptable.
            # Ideally, we'd run client.ask in a thread pool.
            
            response_generator = client.ask(request.message)
            
            for chunk in response_generator:
                if chunk:
                    yield json.dumps({"type": "delta", "content": chunk}) + "\n"
                    # Small sleep to yield control back to event loop if needed
                    await asyncio.sleep(0.01)
            
            yield json.dumps({"type": "done", "content": ""}) + "\n"
            
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
