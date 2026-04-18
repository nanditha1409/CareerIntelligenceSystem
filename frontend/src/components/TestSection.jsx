import React, { useState, useEffect } from 'react';
import { buildAuthHeaders } from '../utils/auth';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const Spinner = ({ size = 8 }) => (
  <svg className={`h-${size} w-${size} animate-spin text-indigo-500`} fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
  </svg>
);

// Change: mirror backend proportional weighting logic for immediate UI feedback while loading.
const calculateQuestionDistribution = (skillsProfile = {}, totalQuestions = 10) => {
  const entries = Object.entries(skillsProfile || {});
  if (!entries.length) return { General: totalQuestions };

  const totalUnits = entries.reduce((sum, [, level]) => sum + Math.max(1, Number(level) || 1), 0);
  if (!totalUnits) return { General: totalQuestions };

  const distribution = {};
  const remainders = [];

  for (const [skill, level] of entries) {
    const fraction = (Math.max(1, Number(level) || 1) / totalUnits) * totalQuestions;
    distribution[skill] = Math.round(fraction);
    remainders.push([skill, fraction - Math.floor(fraction)]);
  }

  Object.keys(distribution).forEach((skill) => {
    if (distribution[skill] <= 0) distribution[skill] = 1;
  });

  let currentTotal = Object.values(distribution).reduce((a, b) => a + b, 0);
  if (currentTotal > totalQuestions) {
    for (const [skill] of Object.entries(distribution).sort((a, b) => b[1] - a[1])) {
      while (currentTotal > totalQuestions && distribution[skill] > 1) {
        distribution[skill] -= 1;
        currentTotal -= 1;
      }
      if (currentTotal === totalQuestions) break;
    }
  } else if (currentTotal < totalQuestions) {
    for (const [skill] of remainders.sort((a, b) => b[1] - a[1])) {
      if (currentTotal >= totalQuestions) break;
      distribution[skill] += 1;
      currentTotal += 1;
    }
  }

  while (Object.values(distribution).reduce((a, b) => a + b, 0) < totalQuestions) {
    const first = Object.keys(distribution)[0];
    distribution[first] += 1;
  }
  while (Object.values(distribution).reduce((a, b) => a + b, 0) > totalQuestions) {
    for (const skill of Object.keys(distribution)) {
      if (distribution[skill] > 1 && Object.values(distribution).reduce((a, b) => a + b, 0) > totalQuestions) {
        distribution[skill] -= 1;
      }
    }
  }

  return distribution;
};

// ── Main ──────────────────────────────────────────────────────────────────────
// skills: { [skillName]: proficiency } OR string[] (legacy)
const TestSection = ({ domain, skills = {}, onComplete, onBack, token, user }) => {
  const [questions, setQuestions]     = useState([]);
  const [answers, setAnswers]         = useState({});
  const [loading, setLoading]         = useState(true);
  const [fetchError, setFetchError]   = useState(null);
  const [submitting, setSubmitting]   = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [isLLM, setIsLLM]             = useState(false);
  const [questionDistribution, setQuestionDistribution] = useState({});

  // Normalise skills to object form
  const skillsObj = Array.isArray(skills)
    ? Object.fromEntries(skills.map((s) => [s, 3]))
    : (skills || {});

  // ── Fetch questions ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!domain) return;
    setLoading(true);
    setFetchError(null);
    setAnswers({});

    // Change: pre-compute and show expected skill-wise question breakdown during generation.
    setQuestionDistribution(calculateQuestionDistribution(skillsObj, 10));

    // Pass skills as JSON query param so backend can generate LLM questions
    const skillsParam = Object.keys(skillsObj).length
      ? `?skills=${encodeURIComponent(JSON.stringify(skillsObj))}`
      : '';

    fetch(`${API}/questions/${encodeURIComponent(domain)}${skillsParam}`, {
      headers: buildAuthHeaders(token),
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        // Addition: attach a unique client-side ID so answer state stays isolated
        // even if upstream question IDs are duplicated or reused.
        const qs = (data.questions || []).map((question, index) => ({
          ...question,
          _clientId: `${domain}-${question.id || 'question'}-${index}`,
        }));
        if (qs.length === 0) throw new Error('Server returned 0 questions for this domain.');
        setQuestions(qs);
        setIsLLM(data.source === 'llm');
        // Change: prefer backend-confirmed distribution when available.
        if (data.question_distribution && typeof data.question_distribution === 'object') {
          setQuestionDistribution(data.question_distribution);
        }
      })
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, [domain, token, JSON.stringify(skillsObj)]);

  // Change: render loading message requested by spec with dynamic breakdown text.
  const distributionSummary = Object.entries(questionDistribution)
    .map(([skill, count]) => `${count} question${count !== 1 ? 's' : ''} for ${skill}`)
    .join(', ');

  const handleAnswer = (questionId, optionIndex) =>
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError(null);

    const answersPayload = questions.map((q) => ({
      id:     q.id,
      answer: answers[q._clientId] ?? -1,
    }));

    try {
      const res = await fetch(`${API}/evaluate`, {
        method:  'POST',
        headers: buildAuthHeaders(token, { 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          domain,
          answers: answersPayload,
          skills: skillsObj,
          user_id: user?.id ? String(user.id) : null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      onComplete(await res.json());
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const answered    = questions.filter((q) => answers[q._clientId] !== undefined).length;
  const total       = questions.length;
  const allAnswered = total > 0 && answered === total;
  const progress    = total ? Math.round((answered / total) * 100) : 0;

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
            {isLLM && (
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-[10px] font-medium text-indigo-300">
                <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
                AI-personalised questions
              </span>
            )}
          </div>
          <button onClick={onBack} className="btn-ghost text-xs shrink-0">← Back</button>
        </div>
      </div>

      {/* LLM loading state */}
      {loading && (
        <div className="glass p-12 flex flex-col items-center gap-5 text-center">
          <Spinner size={10} />
          <div>
            <p className="text-white font-semibold">
              {Object.keys(skillsObj).length
                ? 'Generating Assessment'
                : 'Loading questions…'}
            </p>
            {Object.keys(skillsObj).length > 0 && (
              <p className="mt-1 text-xs text-slate-500">
                {distributionSummary
                  ? `Crafting your test: ${distributionSummary}...`
                  : 'The AI is tailoring questions to your proficiency levels. This takes a few seconds.'}
              </p>
            )}
          </div>
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

          <div className="space-y-5">
            {questions.map((q, index) => {
              const isAnswered = answers[q._clientId] !== undefined;
              return (
                <div
                  key={q._clientId}
                  className={`rounded-3xl border p-6 transition-all duration-200 ${
                    isAnswered
                      ? 'border-indigo-500/30 bg-indigo-950/30'
                      : 'border-white/[0.07] bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-start gap-3 mb-4">
                    <span className={`shrink-0 flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold
                      ${isAnswered ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <span className="inline-block rounded-full bg-slate-800 px-2.5 py-0.5 text-[10px] font-medium text-slate-400 mb-2">
                        {q.topic_tag || q.sub_topic}
                      </span>
                      <h3 className="text-sm font-semibold text-white leading-snug">
                        {q.text || q.question}
                      </h3>
                    </div>
                  </div>

                  <div className="grid gap-2 sm:grid-cols-2">
                    {(q.options || []).map((opt, i) => (
                      <button
                        key={i}
                        onClick={() => handleAnswer(q._clientId, i)}
                        className={`rounded-2xl border px-4 py-3 text-left text-sm transition-all duration-150 ${
                          answers[q._clientId] === i
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
                {submitting
                  ? <><Spinner size={4} /><span>Scoring…</span></>
                  : 'Submit Test'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TestSection;
