"""
Ollama Phi-3 integration.

This service is intentionally isolated from the existing consultant chat so
the new chatbot feature can fail independently without affecting other flows.
"""

import requests
import json
from typing import Iterator

def query_phi3(prompt: str) -> str:
    # Addition: safe Ollama wrapper with graceful fallback for local model failures.
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("response", "") or "AI service unavailable"
    except Exception:
        return "AI service unavailable"

def stream_phi3(prompt: str, system_prompt: str = "") -> Iterator[str]:
    """
    Stream tokens from local Ollama Phi-3.
    """
    try:
        # Combine system prompt and user prompt if provided
        full_prompt = f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": full_prompt,
                "stream": True,
            },
            stream=True,
            timeout=60,
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                yield chunk.get("response", "")
                if chunk.get("done"):
                    break
    except Exception as e:
        yield f"AI service unavailable: {str(e)}"
