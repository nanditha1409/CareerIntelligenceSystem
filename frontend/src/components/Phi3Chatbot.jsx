import React, { useEffect, useRef, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Addition: standalone Phi-3 chatbot that does not share state or transport
// with the existing consultant chat component.
const Phi3Chatbot = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Hi! I am your Phi-3 assistant. Ask me anything about careers, coding practice, or interview preparation.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async () => {
    const userMessage = input.trim();
    if (!userMessage || loading) return;

    setInput('');
    setLoading(true);
    setMessages((prev) => [...prev, { role: 'user', text: userMessage }]);

    try {
      const response = await fetch(`${API}/api/chat/phi3`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: data.response || 'Service unavailable' },
      ]);
    } catch {
      // Addition: UI-safe fallback so chatbot failures never crash the app.
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Service unavailable' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Addition: separate floating toggle keeps the Phi-3 feature modular and independent. */}
      <button
        onClick={() => setOpen((value) => !value)}
        className="fixed bottom-6 left-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-slate-800 shadow-lg shadow-black/30 hover:bg-slate-700 transition-colors"
        aria-label="Toggle Phi-3 chatbot"
      >
        {open ? (
          <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3.75h6m-7.5 8.25h10.125c1.243 0 2.25-1.007 2.25-2.25V6.75c0-1.243-1.007-2.25-2.25-2.25H6.375c-1.243 0-2.25 1.007-2.25 2.25V18A2.25 2.25 0 006.375 20.25z" />
          </svg>
        )}
      </button>

      {open && (
        <div className="fixed bottom-24 left-6 z-50 w-[360px] max-h-[520px] flex flex-col rounded-3xl border border-slate-700/60 bg-slate-900/95 backdrop-blur-xl shadow-2xl shadow-black/40 animate-slide-up">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-700/50">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-700/70 border border-slate-600/60">
              <svg className="h-4 w-4 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.143 2.143 0 01-.627 1.515L5.25 14.207M14.25 3.104v5.714c0 .568.226 1.112.627 1.515l3.873 3.874M3.75 20.25h16.5" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-semibold text-white">Phi-3 Chatbot</p>
              <p className="text-[10px] text-slate-500">Ollama local model</p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 min-h-0">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    message.role === 'user'
                      ? 'bg-indigo-500/20 border border-indigo-500/30 text-slate-100'
                      : 'bg-slate-800/80 border border-slate-700/50 text-slate-200'
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed bg-slate-800/80 border border-slate-700/50 text-slate-200">
                  Thinking...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="px-4 pb-4 pt-2 border-t border-slate-700/50">
            <div className="flex items-center gap-2 rounded-2xl border border-slate-700/60 bg-slate-800/60 px-3 py-2">
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && sendMessage()}
                placeholder="Ask Phi-3 anything..."
                disabled={loading}
                className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-500 disabled:opacity-40 hover:bg-indigo-400 transition-colors"
                aria-label="Send Phi-3 message"
              >
                <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Phi3Chatbot;
