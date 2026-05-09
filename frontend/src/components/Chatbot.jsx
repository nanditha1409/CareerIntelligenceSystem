import React, { useEffect, useRef, useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// ── Static content ─────────────────────────────────────────────────────────

const WELCOME_TEXT =
  "Hi! I'm your Career Assistant. I can help you with career paths, skill-building strategies, interview preparation, and salary expectations across the 9 supported tech domains. What would you like to know?";

const QUICK_PROMPTS = [
  { label: '🚀 Career roadmap', text: 'Give me a career roadmap for becoming an AI/ML Engineer.' },
  { label: '🛠️ Top skills to learn', text: 'What are the most in-demand skills right now across tech domains?' },
  { label: '💰 Salary expectations', text: 'What salary can I expect as a fresher in Data Science?' },
  { label: '🎯 Interview prep', text: 'How should I prepare for a Full Stack Developer interview?' },
  { label: '📊 Domain comparison', text: 'Compare Data Scientist vs Data Analyst roles.' },
  { label: '⏱️ Job-ready timeline', text: 'How long does it take to become job-ready as a DevOps Engineer?' },
];

// ── Bot avatar ─────────────────────────────────────────────────────────────

const BotAvatar = () => (
  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-glow-sm">
    <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
    </svg>
  </div>
);

// ── Message bubble ─────────────────────────────────────────────────────────

const Message = ({ sender, text, streaming }) => {
  const isUser = sender === 'user';
  return (
    <div className={`flex items-end gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      {!isUser && <BotAvatar />}
      {isUser && (
        <div className="flex-shrink-0 h-8 w-8 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center">
          <svg className="h-4 w-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'rounded-br-sm bg-indigo-600 text-white shadow-md shadow-indigo-900/30'
            : 'rounded-bl-sm bg-slate-800/90 border border-slate-700/50 text-slate-200 shadow-sm'
        }`}
      >
        {text}
        {streaming && (
          <span className="inline-block ml-1 h-3.5 w-0.5 bg-indigo-300 animate-pulse align-middle" />
        )}
      </div>
    </div>
  );
};

// ── Typing indicator ────────────────────────────────────────────────────────

const TypingIndicator = () => (
  <div className="flex items-end gap-2.5">
    <BotAvatar />
    <div className="rounded-2xl rounded-bl-sm bg-slate-800/90 border border-slate-700/50 px-4 py-3">
      <div className="flex gap-1 items-center h-4">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  </div>
);

// ── Main component ─────────────────────────────────────────────────────────

const Chatbot = ({ onBack }) => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: WELCOME_TEXT },
  ]);
  const [input, setInput]           = useState('');
  const [streaming, setStreaming]   = useState(false);
  const [showPrompts, setShowPrompts] = useState(true);

  const bottomRef  = useRef(null);
  const inputRef   = useRef(null);
  const historyRef = useRef([]);

  // Scroll to bottom whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const send = async (text) => {
    const userText = (text || input).trim();
    if (!userText || streaming) return;

    setInput('');
    setShowPrompts(false);

    // Add user message immediately
    const userMsg = { sender: 'user', text: userText };
    setMessages((prev) => [...prev, userMsg]);

    // Track history for context (last 6 exchanges)
    historyRef.current = [
      ...historyRef.current.slice(-5),
      { role: 'user', content: userText },
    ];

    setStreaming(true);
    // Seed empty bot bubble
    setMessages((prev) => [...prev, { sender: 'bot', text: '' }]);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          message: userText,
          history: historyRef.current.slice(0, -1).map((h) => ({
            role: h.role,
            content: h.content,
          })),
        }),
      });

      if (!res.ok) throw new Error(`Server error ${res.status}`);

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer   = '';
      let botReply = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6).trim();
          if (payload === '[DONE]') break;
          try {
            const { text: chunk } = JSON.parse(payload);
            if (chunk) {
              botReply += chunk;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = { sender: 'bot', text: botReply };
                return updated;
              });
            }
          } catch {
            // skip malformed SSE chunk
          }
        }
      }

      // Store bot reply in history
      if (botReply) {
        historyRef.current = [
          ...historyRef.current,
          { role: 'assistant', content: botReply },
        ];
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          sender: 'bot',
          text: `Sorry, I couldn't connect to the AI service right now. Please try again in a moment. (${err.message})`,
        };
        return updated;
      });
    } finally {
      setStreaming(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const clearChat = () => {
    setMessages([{ sender: 'bot', text: WELCOME_TEXT }]);
    historyRef.current = [];
    setShowPrompts(true);
    setInput('');
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] max-h-[820px] min-h-[500px] animate-slide-up">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="glass rounded-3xl rounded-b-none border-b-0 px-6 py-5 flex items-center justify-between gap-4 shrink-0">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-700 text-slate-400 hover:text-white hover:border-indigo-500/50 transition-colors"
              aria-label="Go back"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </button>
          )}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-glow-sm">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
            </div>
            <div>
              <h2 className="text-base font-semibold text-white leading-tight">Career AI Chat</h2>
              <p className="text-[11px] text-slate-500 leading-tight">
                Ask anything about tech careers
              </p>
            </div>
          </div>
        </div>

        {/* Online indicator + clear */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-medium text-emerald-400">Online</span>
          </div>
          <button
            onClick={clearChat}
            className="rounded-xl border border-slate-700 bg-slate-800/60 px-3 py-1.5 text-[11px] text-slate-400 hover:text-white hover:border-slate-600 transition-colors"
            aria-label="Clear chat"
          >
            Clear
          </button>
        </div>
      </div>

      {/* ── Message list ────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto glass rounded-none border-t-0 border-b-0 px-6 py-6 space-y-5 min-h-0 scroll-smooth">

        {messages.map((msg, i) => (
          <Message
            key={i}
            sender={msg.sender}
            text={msg.text}
            streaming={streaming && i === messages.length - 1 && msg.sender === 'bot'}
          />
        ))}

        {/* Typing indicator — show while waiting for first token */}
        {streaming && messages[messages.length - 1]?.text === '' && (
          <TypingIndicator />
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Quick prompts ────────────────────────────────────────────────── */}
      {showPrompts && (
        <div className="glass rounded-none border-t-0 border-b-0 px-6 py-4 shrink-0">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-3">
            Quick prompts
          </p>
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((p) => (
              <button
                key={p.text}
                onClick={() => send(p.text)}
                disabled={streaming}
                className="rounded-full border border-slate-700/60 bg-slate-800/60 px-3 py-1.5 text-[11px] text-slate-300 hover:border-indigo-500/50 hover:text-white hover:bg-indigo-500/10 transition-all disabled:opacity-50"
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Input row ───────────────────────────────────────────────────── */}
      <div className="glass rounded-3xl rounded-t-none border-t-0 px-4 py-4 shrink-0">
        <div
          className={`flex items-center gap-3 rounded-2xl border px-4 py-3 transition-all duration-200 ${
            input
              ? 'border-indigo-500/50 bg-slate-900/80 ring-1 ring-indigo-500/20'
              : 'border-slate-700/60 bg-slate-900/50'
          }`}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about careers, skills, salaries, interview tips…"
            disabled={streaming}
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none disabled:opacity-60"
            aria-label="Chat input"
          />

          {/* Character hint */}
          {input.length > 0 && (
            <span className="text-[10px] text-slate-600 shrink-0 hidden sm:block">
              Enter ↵
            </span>
          )}

          {/* Send button */}
          <button
            onClick={() => send()}
            disabled={!input.trim() || streaming}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:scale-105 shadow-md shadow-indigo-900/40"
            aria-label="Send message"
          >
            {streaming ? (
              <svg className="h-3.5 w-3.5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            ) : (
              <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            )}
          </button>
        </div>
        <p className="mt-2 text-[10px] text-center text-slate-600">
          Powered by NextStep AI · Covers 9 tech career domains
        </p>
      </div>
    </div>
  );
};

export default Chatbot;
