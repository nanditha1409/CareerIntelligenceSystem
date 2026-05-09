import React, { useState, useEffect, useCallback } from 'react';
import { buildAuthHeaders } from '../utils/auth';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const LANGUAGE_KEYWORDS = {
  python: new Set(['def', 'return', 'for', 'while', 'if', 'else', 'elif', 'True', 'False', 'in', 'pass']),
  java: new Set(['public', 'class', 'static', 'int', 'boolean', 'String', 'return', 'for', 'while', 'if', 'else', 'true', 'false']),
};

const Spinner = ({ size = 8 }) => (
  <svg className={`h-${size} w-${size} animate-spin text-indigo-500`} fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
  </svg>
);

const renderHighlightedCode = (code, language) => {
  const keywords = LANGUAGE_KEYWORDS[language] || new Set();
  return code.split('\n').map((line, lineIndex) => (
    <div key={`${language}-${lineIndex}`} className="whitespace-pre-wrap break-words">
      {line.split(/(\W+)/).map((token, tokenIndex) => {
        if (keywords.has(token)) {
          return <span key={tokenIndex} className="text-indigo-300">{token}</span>;
        }
        if (/^\d+$/.test(token)) {
          return <span key={tokenIndex} className="text-amber-300">{token}</span>;
        }
        if (/^["'`].*["'`]$/.test(token)) {
          return <span key={tokenIndex} className="text-emerald-300">{token}</span>;
        }
        return <span key={tokenIndex} className="text-slate-300">{token}</span>;
      })}
    </div>
  ));
};

// ── Main ──────────────────────────────────────────────────────────────────────
const TestSection = ({ domain, skills = {}, onComplete, onBack, token, user }) => {
  const [questions, setQuestions]     = useState([]);
  const [answers, setAnswers]         = useState({});
  const [loading, setLoading]         = useState(true);
  const [fetchError, setFetchError]   = useState(null);
  const [submitting, setSubmitting]   = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [isLLM, setIsLLM]             = useState(false);
  const [assessmentLevel, setAssessmentLevel] = useState('easy');
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  // retryCount bumps to force the useEffect to re-run on Retry click
  const [retryCount, setRetryCount]   = useState(0);

  // Normalise skills to object form
  const skillsObj = Array.isArray(skills)
    ? Object.fromEntries(skills.map((s) => [s, 3]))
    : (skills || {});

  // ── Fetch questions ─────────────────────────────────────────────────────────
  const fetchQuestions = useCallback(() => {
    if (!domain) return;
    setLoading(true);
    setFetchError(null);
    setQuestions([]);
    setAnswers({});

    const params = new URLSearchParams();
    params.set('level', assessmentLevel);
    if (Object.keys(skillsObj).length) {
      params.set('skills', JSON.stringify(skillsObj));
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';

    fetch(`${API}/questions/${encodeURIComponent(domain)}${queryString}`, {
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
        const qs = (data.questions || []).map((q, idx) => ({
          ...q,
          // Stable client-side key — avoids stale answer state on re-fetch
          _clientId: `${domain}-${q.id || idx}-${idx}`,
        }));
        if (qs.length === 0) {
          setFetchError('No questions available for this domain. Please try another.');
          return;
        }
        setQuestions(qs);
        setIsLLM(data.source === 'llm');
      })
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessmentLevel, domain, token, retryCount]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  // ── Answer selection ────────────────────────────────────────────────────────
  const handleAnswer = (clientId, optionIndex) =>
    setAnswers((prev) => ({ ...prev, [clientId]: optionIndex }));

  const handleCodeAnswer = (clientId, language, value) =>
    setAnswers((prev) => ({
      ...prev,
      [clientId]: {
        ...(typeof prev[clientId] === 'object' && prev[clientId] !== null ? prev[clientId] : {}),
        [language]: value,
      },
    }));

  // ── Submit ──────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError(null);

    // Send answers as a plain dict {questionId: selectedIndex}
    // Backend _parse_answers() accepts this directly
    const answersDict = {};
    questions.forEach((q) => {
      const qid = q.id || q._clientId;
      if (q.type === 'coding') {
        answersDict[qid] = answers[q._clientId]?.[selectedLanguage] ?? '';
      } else {
        answersDict[qid] = answers[q._clientId] ?? -1;
      }
    });

    try {
      const res = await fetch(`${API}/evaluate`, {
        method:  'POST',
        headers: buildAuthHeaders(token, { 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          domain,
          answers: answersDict,
          assessment_level: assessmentLevel,
          programming_language: assessmentLevel === 'medium' ? selectedLanguage : null,
          skills:  skillsObj,
          user_id: user?.id ? String(user.id) : null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      onComplete(await res.json());
    } catch (err) {
      setSubmitError(err?.message || String(err) || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const answered    = questions.filter((q) => {
    const answer = answers[q._clientId];
    return q.type === 'coding'
      ? typeof answer?.[selectedLanguage] === 'string' && answer[selectedLanguage].trim().length > 0
      : answer !== undefined;
  }).length;
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
                ? assessmentLevel === 'medium'
                  ? `Solve all ${total} coding challenges to reveal your readiness score.`
                  : `Answer all ${total} questions to reveal your readiness score.`
                : 'Loading questions…'}
            </p>
            {isLLM && (
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-[10px] font-medium text-indigo-300">
                <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
                AI-personalised questions
              </span>
            )}
            <div className="mt-4 inline-flex rounded-2xl border border-slate-700/70 bg-slate-950/60 p-1">
              {[
                { value: 'easy', label: 'Easy MCQ' },
                { value: 'medium', label: 'Medium Coding' },
              ].map((level) => (
                <button
                  key={level.value}
                  type="button"
                  onClick={() => {
                    setAssessmentLevel(level.value);
                    setRetryCount((count) => count + 1);
                  }}
                  className={`rounded-xl px-4 py-2 text-xs font-semibold transition-all duration-200 ${
                    assessmentLevel === level.value
                      ? 'bg-indigo-500 text-white shadow-glow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {level.label}
                </button>
              ))}
            </div>
            {assessmentLevel === 'medium' && (
              <div className="mt-3 flex items-center gap-3">
                <label htmlFor="medium-language" className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Language
                </label>
                <select
                  id="medium-language"
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="rounded-xl border border-slate-700/70 bg-slate-950/80 px-3 py-2 text-xs font-semibold text-slate-200 outline-none transition-colors focus:border-indigo-500/60"
                >
                  <option value="python">Python</option>
                  <option value="java">Java</option>
                </select>
              </div>
            )}
          </div>
          <button onClick={onBack} className="btn-ghost text-xs shrink-0">← Back</button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="glass p-12 flex flex-col items-center gap-5 text-center">
          <Spinner size={10} />
          <p className="text-white font-semibold">Loading questions…</p>
          <p className="text-xs text-slate-500">Fetching your personalised assessment</p>
        </div>
      )}

      {/* Fetch error */}
      {!loading && fetchError && (
        <div className="glass p-8 text-center space-y-4">
          <p className="text-rose-400 font-semibold">Failed to load questions</p>
          <p className="text-sm text-slate-400">{fetchError}</p>
          <button
            onClick={() => setRetryCount((c) => c + 1)}
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
              const isAnswered = q.type === 'coding'
                ? Boolean(answers[q._clientId]?.[selectedLanguage]?.trim())
                : answers[q._clientId] !== undefined;
              const starterCode = q.type === 'coding'
                ? (q.starter_code_map?.[selectedLanguage] || '')
                : '';
              const editorValue = q.type === 'coding'
                ? (answers[q._clientId]?.[selectedLanguage] ?? '')
                : '';
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
                        {q.topic_tag || q.sub_topic || 'General'}
                      </span>
                      <h3 className="text-sm font-semibold text-white leading-snug">
                        {q.text || q.question}
                      </h3>
                    </div>
                  </div>

                  {q.type === 'coding' ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3">
                        <div>
                          <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Medium challenge</p>
                          <p className="mt-1 text-xs text-slate-300">{selectedLanguage === 'python' ? 'Python' : 'Java'} answer</p>
                        </div>
                        <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-[10px] font-semibold text-indigo-300">
                          Type working code
                        </span>
                      </div>

                      {starterCode && (
                        <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                          <p className="mb-2 text-[10px] uppercase tracking-[0.18em] text-slate-500">Starter code</p>
                          <pre className="overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-slate-300">
                            {starterCode}
                          </pre>
                        </div>
                      )}

                      <textarea
                        value={editorValue}
                        onChange={(e) => handleCodeAnswer(q._clientId, selectedLanguage, e.target.value)}
                        className="min-h-[220px] w-full rounded-2xl border border-slate-700/60 bg-slate-950/80 px-4 py-4 font-mono text-sm text-slate-100 outline-none transition-colors focus:border-indigo-500/60"
                        spellCheck={false}
                        placeholder={selectedLanguage === 'python' ? 'def solve(...):\n    pass' : 'public class Solution {\n    public static void main(String[] args) {\n    }\n}'}
                      />

                      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                        <p className="mb-2 text-[10px] uppercase tracking-[0.18em] text-slate-500">Syntax preview</p>
                        <div className="min-h-[120px] overflow-x-auto font-mono text-xs leading-6">
                          {editorValue.trim()
                            ? renderHighlightedCode(editorValue, selectedLanguage)
                            : <span className="text-slate-500">Start typing to preview {selectedLanguage === 'python' ? 'Python' : 'Java'} syntax styling.</span>}
                        </div>
                      </div>
                    </div>
                  ) : (
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
                <p className="mt-2 text-xs text-slate-600">
                  {assessmentLevel === 'medium'
                    ? `Coding answers run in a ${selectedLanguage === 'python' ? 'Python' : 'Java'} sandbox against test cases.`
                    : 'Easy mode uses multiple-choice questions.'}
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
