import React, { useState, useEffect } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const LEVELS = [
  { value: 'mixed', label: 'Mixed', helper: '5 easy, 3 medium, 2 hard' },
  { value: 'easy', label: 'Easy', helper: '10 basic MCQs' },
  { value: 'medium', label: 'Medium', helper: 'Includes 2 easy coding prompts' },
  { value: 'hard', label: 'Hard', helper: 'Includes 3 medium coding prompts' },
];

const LEVEL_STYLE = {
  easy: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300',
  medium: 'border-amber-500/25 bg-amber-500/10 text-amber-300',
  hard: 'border-rose-500/25 bg-rose-500/10 text-rose-300',
};

// ── Spinner ───────────────────────────────────────────────────────────────────
const Spinner = () => (
  <svg className="h-8 w-8 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
  </svg>
);

// ── Main ──────────────────────────────────────────────────────────────────────
const TestSection = ({ domain, skills = [], currentUser, onComplete, onBack }) => {
  const [questions, setQuestions]   = useState([]);
  const [answers, setAnswers]       = useState({});   // { [questionId]: chosenOption }
  const [loading, setLoading]       = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [level, setLevel] = useState('mixed');
  const [levelMix, setLevelMix] = useState({});

  // ── Fetch questions ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!domain) return;
    setLoading(true);
    setFetchError(null);
    setAnswers({});

    // Try new path first, fall back to legacy
    const params = new URLSearchParams({
      level,
      user_id: currentUser?.user_id || 'guest',
    });

    fetch(`${API}/questions/${encodeURIComponent(domain)}?${params.toString()}`)
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        const qs = data.questions || [];
        if (qs.length === 0) throw new Error('Server returned 0 questions for this domain.');
        setQuestions(qs);
        setLevelMix(data.level_mix || {});
      })
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, [domain, level, currentUser?.user_id]);

  // ── Answer selection ────────────────────────────────────────────────────────
  const handleAnswer = (questionId, optionIndex) =>
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));

  const handleCodeAnswer = (questionId, code) =>
    setAnswers((prev) => ({ ...prev, [questionId]: code }));

  // ── Submit ──────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError(null);

    // Build structured payload: [{id, answer}] where answer is the chosen index
    const answersPayload = questions.map((q) => ({
      id:     q.id,
      answer: answers[q.id] ?? -1,
    }));

    try {
      const res = await fetch(`${API}/evaluate`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          domain,
          answers: answersPayload,
          skills,
          user_id: currentUser?.user_id ?? null,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      onComplete(data);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // ── Derived state ───────────────────────────────────────────────────────────
  const answered   = questions.filter((q) => {
    const answer = answers[q.id];
    if (q.question_type === 'coding') return typeof answer === 'string' && answer.trim().length > 0;
    return answer !== undefined;
  }).length;
  const total      = questions.length;
  const allAnswered = total > 0 && answered === total;
  const progress   = total ? Math.round((answered / total) * 100) : 0;

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-8 animate-slide-up">

      {/* Header */}
      <div className="glass p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="section-label">Assessment</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">
              Test your readiness for {domain}
            </h2>
            <p className="mt-1.5 text-sm text-slate-400">
              {total > 0
                ? `Answer all ${total} ${level} level questions to reveal your readiness score.`
                : 'Loading questions…'}
            </p>
          </div>
          <button onClick={onBack} className="btn-ghost text-xs shrink-0">← Back</button>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-4">
          {LEVELS.map((item) => (
            <button
              key={item.value}
              onClick={() => setLevel(item.value)}
              className={`rounded-2xl border px-4 py-3 text-left transition-all duration-200 ${
                level === item.value
                  ? 'border-indigo-500 bg-indigo-500/15 text-white shadow-glow-sm'
                  : 'border-slate-700/60 bg-slate-950/50 text-slate-400 hover:border-indigo-500/40 hover:text-slate-200'
              }`}
            >
              <span className="block text-sm font-semibold">{item.label}</span>
              <span className="mt-1 block text-xs opacity-75">{item.helper}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-24">
          <Spinner />
        </div>
      )}

      {/* Fetch error */}
      {!loading && fetchError && (
        <div className="glass p-8 text-center space-y-4">
          <p className="text-rose-400 font-semibold">Failed to load questions</p>
          <p className="text-sm text-slate-400">{fetchError}</p>
          <button
            onClick={() => { setFetchError(null); setLoading(true); }}
            className="btn-primary text-xs"
          >
            Retry
          </button>
        </div>
      )}

      {/* Questions */}
      {!loading && !fetchError && total > 0 && (
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">

          {/* Question cards */}
          <div className="space-y-5">
            {questions.map((q, index) => {
              const isCoding = q.question_type === 'coding';
              const isAnswered = isCoding
                ? typeof answers[q.id] === 'string' && answers[q.id].trim().length > 0
                : answers[q.id] !== undefined;
              return (
                <div
                  key={q.id}
                  className={`rounded-3xl border p-6 transition-all duration-200 ${
                    isAnswered
                      ? 'border-indigo-500/30 bg-indigo-950/30'
                      : 'border-white/[0.07] bg-slate-900/60'
                  }`}
                >
                  {/* Question meta */}
                  <div className="flex items-start gap-3 mb-4">
                    <span className={`shrink-0 flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold
                      ${isAnswered ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <span className="inline-block rounded-full bg-slate-800 px-2.5 py-0.5 text-[10px] font-medium text-slate-400 mb-2">
                        {q.topic_tag || q.sub_topic}
                      </span>
                      <span className={`ml-2 inline-block rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] ${LEVEL_STYLE[q.difficulty] || LEVEL_STYLE.easy}`}>
                        {q.difficulty || 'easy'}
                      </span>
                      {q.question_type && (
                        <span className="ml-2 inline-block rounded-full border border-slate-700/60 bg-slate-950/50 px-2.5 py-0.5 text-[10px] font-medium text-slate-500">
                          {q.question_type}
                        </span>
                      )}
                      <h3 className="text-sm font-semibold text-white leading-snug">{q.question}</h3>
                    </div>
                  </div>

                  {isCoding ? (
                    <div className="space-y-3">
                      {q.starter_code && (
                        <div className="rounded-2xl border border-slate-700/60 bg-slate-950/70 p-4">
                          <p className="mb-2 text-[10px] uppercase tracking-wider text-slate-500">Starter code</p>
                          <pre className="overflow-x-auto whitespace-pre-wrap text-xs leading-relaxed text-slate-300">
                            <code>{q.starter_code}</code>
                          </pre>
                        </div>
                      )}
                      <textarea
                        value={answers[q.id] ?? q.starter_code ?? ''}
                        onChange={(event) => handleCodeAnswer(q.id, event.target.value)}
                        spellCheck="false"
                        className="min-h-[220px] w-full rounded-2xl border border-slate-700/70 bg-slate-950/70 px-4 py-3 font-mono text-sm leading-relaxed text-slate-100 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                        placeholder="Write your code or pseudocode here..."
                      />
                      <p className="text-xs text-slate-500">
                        Coding answers are reviewed with lightweight keyword-based scoring for now, so include clear logic and important function/operation names.
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-2 sm:grid-cols-2">
                      {(q.options || []).map((opt, i) => (
                        <button
                          key={i}
                          onClick={() => handleAnswer(q.id, i)}
                          className={`rounded-2xl border px-4 py-3 text-left text-sm transition-all duration-150 ${
                            answers[q.id] === i
                              ? 'border-indigo-500 bg-indigo-500/15 text-white font-medium'
                              : 'border-slate-700/60 bg-slate-950/50 text-slate-400 hover:border-indigo-500/40 hover:text-slate-200'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Sticky sidebar */}
          <div>
            <div className="glass p-6 sticky top-24 space-y-5">
              <div>
                <p className="section-label">Progress</p>
                <div className="mt-4 flex items-end gap-2">
                  <span className="text-4xl font-bold text-white">{answered}</span>
                  <span className="text-slate-500 mb-1">/ {total}</span>
                </div>
                <div className="mt-3 h-2 w-full rounded-full bg-slate-800">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {allAnswered
                    ? 'All answered — ready to submit.'
                    : `${total - answered} question${total - answered !== 1 ? 's' : ''} remaining`}
                </p>
              </div>

              {Object.keys(levelMix).length > 0 && (
                <div className="rounded-2xl border border-slate-700/60 bg-slate-950/50 p-4">
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-3">Question mix</p>
                  <div className="space-y-2">
                    {Object.entries(levelMix).map(([difficulty, count]) => (
                      <div key={difficulty} className="flex items-center justify-between text-xs">
                        <span className="capitalize text-slate-400">{difficulty}</span>
                        <span className="font-semibold text-slate-200">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Submit error */}
              {submitError && (
                <p className="rounded-2xl bg-rose-500/10 border border-rose-500/20 px-4 py-3 text-xs text-rose-300">
                  {submitError}
                </p>
              )}

              <button
                onClick={handleSubmit}
                disabled={!allAnswered || submitting}
                className="btn-primary w-full"
              >
                {submitting ? (
                  <><Spinner /><span>Scoring…</span></>
                ) : 'Submit Test'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TestSection;
