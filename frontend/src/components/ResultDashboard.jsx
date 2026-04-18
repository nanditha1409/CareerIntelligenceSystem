import React from 'react';
import ProgressRing from './ProgressRing';

// ── Helpers ───────────────────────────────────────────────────────────────────

const MiniBar = ({ label, value, color }) => {
  const safe = Number.isFinite(value) ? Math.min(100, Math.max(0, value)) : 0;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-slate-500">{label}</span>
        <span className="font-semibold text-slate-200">{safe}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-slate-800">
        <div
          className={`h-1.5 rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${safe}%` }}
        />
      </div>
    </div>
  );
};

const WeakTopicRow = ({ sub_topic, wrong, total }) => {
  const pct = total > 0 ? Math.round((wrong / total) * 100) : 0;
  return (
    <div className="flex items-center justify-between rounded-2xl bg-slate-950/60 px-4 py-3 gap-3">
      <div className="flex items-center gap-2.5 min-w-0">
        <span className="h-2 w-2 rounded-full bg-rose-400 shrink-0" />
        <span className="text-sm text-slate-300 truncate">{sub_topic}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <div className="h-1.5 w-16 rounded-full bg-slate-800">
          <div className="h-1.5 rounded-full bg-rose-500" style={{ width: `${pct}%` }} />
        </div>
        <span className="text-xs font-semibold text-rose-400 w-14 text-right">
          {wrong}/{total} wrong
        </span>
      </div>
    </div>
  );
};

// ── Main ──────────────────────────────────────────────────────────────────────

const ResultDashboard = ({ result, domain, onRetake, onNewSearch }) => {
  if (!result) return null;

  // ── Safe field extraction ─────────────────────────────────────────────────
  const quizScore      = Number.isFinite(result.quiz_score) ? result.quiz_score
                       : Number.isFinite(result.score)      ? result.score
                       : 0;

  const correctCount   = Number.isFinite(result.correct_count) ? result.correct_count : null;
  const totalQuestions = Number.isFinite(result.total_questions) ? result.total_questions : 10;

  const readiness      = result.readiness || {};
  const readinessScore = Number.isFinite(readiness.readiness_score) ? readiness.readiness_score : quizScore;
  const skillMatch     = Number.isFinite(readiness.skill_match)     ? readiness.skill_match     : 0;
  const assessPerf     = Number.isFinite(readiness.assessment_performance) ? readiness.assessment_performance : quizScore;
  const readinessLabel = readiness.label || '';
  const weakSubTopics  = Array.isArray(result.weak_sub_topics) ? result.weak_sub_topics : [];
  const weakAreas      = Array.isArray(result.weak_areas)      ? result.weak_areas      : [];
  const resources      = Array.isArray(result.resources)       ? result.resources       : [];

  // ── Colours ───────────────────────────────────────────────────────────────
  const quizColor =
    quizScore >= 80 ? '#34D399' :
    quizScore >= 50 ? '#FBBF24' : '#F87171';

  const readinessLabelClass =
    readinessLabel === 'Job Ready'  ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/25' :
    readinessLabel === 'Developing' ? 'text-amber-400  bg-amber-400/10  border-amber-400/25'  :
                                      'text-rose-400   bg-rose-400/10   border-rose-400/25';

  const quizLabel =
    quizScore >= 80 ? 'Strong performance' :
    quizScore >= 50 ? 'Room to improve'    : 'Needs more practice';

  return (
    <div className="space-y-8 animate-slide-up">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="glass p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="section-label">Results</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">{domain} assessment</h2>
            <p className="mt-1.5 text-sm text-slate-400">
              Readiness = (0.6 × Skill Match) + (0.4 × Quiz Score)
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={onRetake}    className="btn-ghost text-xs">Retake test</button>
            <button onClick={onNewSearch} className="btn-primary text-xs">New search</button>
          </div>
        </div>
      </div>

      {/* ── Dual meters ────────────────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">

        {/* Quiz Performance */}
        <div className="glass flex flex-col items-center gap-5 p-8">
          <p className="section-label self-start">Quiz Performance</p>
          <ProgressRing
            value={quizScore}
            size={160}
            strokeWidth={12}
            sublabel="quiz score"
            color={quizColor}
          />
          <div className="w-full text-center space-y-1">
            <p className="text-sm font-semibold text-white">{quizLabel}</p>
            {correctCount !== null && (
              <p className="text-lg font-bold text-indigo-300">
                {correctCount}/{totalQuestions} Correct
              </p>
            )}
            <p className="text-xs text-slate-500">
              Raw score: correct answers ÷ total questions × 100
            </p>
          </div>
        </div>

        {/* Overall Readiness */}
        <div className="glass flex flex-col items-center gap-5 p-8">
          <p className="section-label self-start">Overall Readiness</p>
          <ProgressRing
            value={readinessScore}
            size={160}
            strokeWidth={12}
            sublabel="readiness"
            color="#6366F1"
          />
          {readinessLabel && (
            <span className={`rounded-full border px-4 py-1.5 text-xs font-semibold ${readinessLabelClass}`}>
              {readinessLabel}
            </span>
          )}
          <div className="w-full space-y-3">
            <MiniBar label="Skill Match ×0.6" value={skillMatch}  color="bg-indigo-500" />
            <MiniBar label="Quiz Score  ×0.4" value={assessPerf}  color="bg-violet-500" />
          </div>
        </div>
      </div>

      {/* ── Feedback + Weak sub-topics ──────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">

        {/* Feedback */}
        <div className="glass flex flex-col p-8 gap-6">
          <div>
            <p className="section-label">Feedback</p>
            <p className="mt-3 text-lg font-semibold text-white leading-snug">
              {result.feedback || 'No feedback available.'}
            </p>
          </div>

          {weakAreas.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-3">
                Sub-topics to review
              </p>
              <ul className="space-y-2">
                {weakAreas.map((area, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2.5 rounded-2xl bg-slate-950/60 px-4 py-3 text-sm text-slate-300"
                  >
                    <span className="mt-0.5 text-rose-400 shrink-0">✕</span>
                    {area}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Weak sub-topics */}
        <div className="glass p-8">
          <p className="section-label">Weak Sub-Topics</p>
          <p className="mt-1 text-xs text-slate-500 mb-4">
            Topics where you got more than 40% of questions wrong.
          </p>

          {weakSubTopics.length > 0 ? (
            <div className="space-y-3">
              {weakSubTopics.map((st, i) => (
                <WeakTopicRow key={i} {...st} />
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 px-4 py-3">
              <span className="text-emerald-400 text-lg">✓</span>
              <p className="text-sm text-emerald-300">No critical weak sub-topics detected.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Resources ──────────────────────────────────────────────────────── */}
      {resources.length > 0 && (
        <div className="glass p-8">
          <p className="section-label mb-4">Recommended resources</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {resources.map((r, i) => (
              <a
                key={i}
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start gap-3 rounded-2xl border border-slate-700/60 bg-slate-950/50 p-4
                           transition-all duration-200 hover:border-indigo-500/40 hover:bg-indigo-500/5"
              >
                <div className="min-w-0">
                  <p className="text-[10px] uppercase tracking-wider text-indigo-400 mb-1">{r.skill}</p>
                  <p className="text-sm font-medium text-slate-200 leading-snug group-hover:text-white transition-colors">
                    {r.title}
                  </p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultDashboard;
