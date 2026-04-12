import React, { useState, useEffect } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

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

  // ── Fetch questions ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!domain) return;
    setLoading(true);
    setFetchError(null);
    setAnswers({});

    // Try new path first, fall back to legacy
    fetch(`${API}/questions/${encodeURIComponent(domain)}`)
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
      })
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, [domain]);

  // ── Answer selection ────────────────────────────────────────────────────────
  const handleAnswer = (questionId, optionIndex) =>
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));

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
  const answered   = questions.filter((q) => answers[q.id] !== undefined).length;
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
                ? `Answer all ${total} questions to reveal your readiness score.`
                : 'Loading questions…'}
            </p>
          </div>
          <button onClick={onBack} className="btn-ghost text-xs shrink-0">← Back</button>
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
              const isAnswered = Boolean(answers[q.id]);
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
                      <h3 className="text-sm font-semibold text-white leading-snug">{q.question}</h3>
                    </div>
                  </div>

                  {/* Options */}
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
