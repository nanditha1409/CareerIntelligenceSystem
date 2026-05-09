"""Phi-3 / Ollama service — disabled. Gemini is the sole LLM provider."""

def query_phi3(prompt: str, system: str = "") -> str:
    return "Phi-3 is not configured. Please use the Gemini-powered consultant."

def stream_phi3(prompt: str, system: str = ""):
    yield "Phi-3 is not configured. Please use the Gemini-powered consultant."
