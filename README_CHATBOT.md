## Phi-3 Chatbot Setup

The chatbot uses Phi-3 (3.8B) via Ollama for local inference.

### Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3
ollama serve   # runs on localhost:11434
```

### Fallback

If Ollama is not running, the chatbot automatically falls back to Gemini (requires `GEMINI_API_KEY` in `backend/.env`).

### Is Phi-3 ML?

Yes. Phi-3 is a 3.8B parameter transformer neural network — a generative ML model. The recommendation engine uses scikit-learn supervised classification (separate ML pipeline). The system uses ML at two layers: predictive (sklearn) for domain matching, and generative (Phi-3/LLM) for conversational guidance.
