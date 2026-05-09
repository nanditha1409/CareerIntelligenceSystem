import React, { useState, useEffect } from "react";
import ProgressRing from "./ProgressRing";
import { buildAuthHeaders } from "../utils/auth";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

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
          <div
            className="h-1.5 rounded-full bg-rose-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-xs font-semibold text-rose-400 w-14 text-right">
          {wrong}/{total} wrong
        </span>
      </div>
    </div>
  );
};

// ── Market Rate Card ──────────────────────────────────────────────────────────

const DEMAND_BADGE = {
  "Very High": "text-emerald-400 bg-emerald-400/10 border-emerald-400/25",
  High: "text-sky-400    bg-sky-400/10    border-sky-400/20",
  Medium: "text-amber-400  bg-amber-400/10  border-amber-400/25",
  Low: "text-slate-400  bg-slate-400/10  border-slate-400/20",
};

const CONF_COLOR = (pct) => {
  if (pct >= 80)
    return {
      bar: "bg-emerald-500",
      text: "text-emerald-400",
      ring: "border-emerald-500/30 bg-emerald-500/10",
    };
  if (pct >= 65)
    return {
      bar: "bg-amber-500",
      text: "text-amber-400",
      ring: "border-amber-500/30 bg-amber-500/10",
    };
  return {
    bar: "bg-rose-500",
    text: "text-rose-400",
    ring: "border-rose-500/30 bg-rose-500/10",
  };
};

const MarketRateCard = ({
  domain,
  experienceLevel,
  skills,
  token,
  readinessScore,
  quizScore,
}) => {
  const [rateData, setRateData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!domain) return;
    setLoading(true);
    setError(null);

    fetch(`${API}/api/market-rate`, {
      method: "POST",
      headers: buildAuthHeaders(token, { "Content-Type": "application/json" }),
      body: JSON.stringify({
        domain,
        experience_level: experienceLevel || "no_experience",
        skills: skills || {},
        readiness_score: readinessScore ?? null,
        quiz_score: quizScore ?? null,
      }),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => setRateData(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [domain, experienceLevel, token, readinessScore, quizScore]);

  if (loading) {
    return (
      <div className="glass p-8">
        <p className="section-label">Market Rate Intelligence</p>
        <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 rounded-2xl bg-slate-800/50 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (error || !rateData) return null;

  const conf = rateData.confidence_pct ?? 60;
  const confColors = CONF_COLOR(conf);
  const demandBadge =
    DEMAND_BADGE[rateData.demand_label] || DEMAND_BADGE["Medium"];
  const lower = rateData.range_lpa?.lower ?? rateData.predicted_lpa;
  const upper = rateData.range_lpa?.upper ?? rateData.predicted_lpa;
  const avgSkill = rateData.avg_skill_level ?? 3;
  const skillBarW = Math.min(100, Math.max(0, (avgSkill / 5) * 100));
  const readAdj = rateData.readiness_adjustment_pct ?? null;

  return (
    <div className="glass p-8">
      {/* Header */}
      <div className="mb-6">
        <p className="section-label">Market Rate Intelligence</p>
        <h3 className="mt-2 text-xl font-semibold text-white">
          Estimated salary for {domain}
        </h3>
        <p className="mt-1 text-sm text-slate-400">
          Based on your skills, readiness score, experience level, and current
          market demand.
        </p>
      </div>

      {/* Hero salary range */}
      <div className="mb-6 rounded-2xl border border-indigo-500/25 bg-gradient-to-br from-indigo-950/60 to-slate-900/60 p-6">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-indigo-300/70 mb-1">
              Estimated range
            </p>
            <p className="text-4xl font-extrabold text-white tracking-tight">
              ₹{lower}
              <span className="text-slate-400 mx-2 font-light">–</span>₹{upper}
              <span className="text-lg font-normal text-slate-400 ml-2">
                LPA
              </span>
            </p>
            <p className="mt-2 text-xs text-slate-400">
              Based on current trends for {rateData.experience_label} level ·{" "}
              {rateData.demand_label} demand
            </p>
          </div>
          {/* Confidence badge */}
          <div
            className={`flex flex-col items-center justify-center rounded-2xl border px-5 py-3 shrink-0 ${confColors.ring}`}
          >
            <p className={`text-2xl font-extrabold ${confColors.text}`}>
              {conf}%
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5">
              {rateData.confidence_label}
            </p>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="mt-5">
          <div className="flex justify-between text-[10px] text-slate-500 mb-1.5">
            <span>Prediction confidence</span>
            <span>{conf}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-slate-800">
            <div
              className={`h-1.5 rounded-full transition-all duration-700 ${confColors.bar}`}
              style={{ width: `${conf}%` }}
            />
          </div>
        </div>
      </div>

      {/* Signal breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {/* Market demand */}
        <div className="rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4 flex flex-col gap-2">
          <p className="text-[10px] uppercase tracking-wider text-slate-500">
            Market demand
          </p>
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${demandBadge}`}
            >
              {rateData.demand_label}
            </span>
          </div>
          <p className="text-xs text-slate-400">
            ~{rateData.growth_rate_pct}% YoY growth
          </p>
        </div>

        {/* Skill depth */}
        <div className="rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4 flex flex-col gap-2">
          <p className="text-[10px] uppercase tracking-wider text-slate-500">
            Skill depth
          </p>
          <div className="h-1.5 w-full rounded-full bg-slate-800 mt-1">
            <div
              className="h-1.5 rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-700"
              style={{ width: `${skillBarW}%` }}
            />
          </div>
          <p className="text-xs text-slate-400">
            Avg proficiency {avgSkill.toFixed(1)}/5
          </p>
        </div>

        {/* Readiness adjustment */}
        <div className="rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4 flex flex-col gap-2">
          <p className="text-[10px] uppercase tracking-wider text-slate-500">
            Readiness effect
          </p>
          {readAdj !== null ? (
            <>
              <p
                className={`text-base font-bold ${
                  readAdj > 0
                    ? "text-emerald-400"
                    : readAdj < 0
                      ? "text-rose-400"
                      : "text-slate-300"
                }`}
              >
                {readAdj > 0
                  ? `+${readAdj}%`
                  : readAdj < 0
                    ? `${readAdj}%`
                    : "Neutral"}
              </p>
              <p className="text-xs text-slate-400">
                {rateData.readiness_label}
              </p>
            </>
          ) : (
            <p className="text-xs text-slate-500 mt-1">
              Take a test to include assessment data
            </p>
          )}
        </div>
      </div>

      {/* Insight + improvement message */}
      <div className="space-y-3">
        <div className="rounded-2xl border border-slate-700/40 bg-slate-950/30 px-5 py-4">
          <p className="text-xs text-slate-400 leading-relaxed">
            <span className="text-indigo-400 font-medium">💡 Insight — </span>
            {rateData.insight}
          </p>
        </div>
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 px-5 py-4">
          <p className="text-xs text-emerald-300 leading-relaxed">
            <span className="font-semibold">✨ Growth potential — </span>
            With further skill improvements and higher readiness, the estimated
            salary of{" "}
            <span className="font-semibold text-white">
              {rateData.range_lpa?.formatted}
            </span>{" "}
            for <span className="font-semibold text-emerald-400">{domain}</span>{" "}
            can be achieved.
          </p>
        </div>
      </div>
    </div>
  );
};

// ── Main ──────────────────────────────────────────────────────────────────────

const ResultDashboard = ({
  result,
  domain,
  recommendations = [],
  onRetake,
  onNewSearch,
  token,
  skills = {},
  experienceLevel = "no_experience",
}) => {
  if (!result) return null;

  // ── Safe field extraction ─────────────────────────────────────────────────
  const quizScore = Number.isFinite(result.quiz_score)
    ? result.quiz_score
    : Number.isFinite(result.score)
      ? result.score
      : 0;

  const correctCount = Number.isFinite(result.correct_count)
    ? result.correct_count
    : null;
  const totalQuestions = Number.isFinite(result.total_questions)
    ? result.total_questions
    : 10;
  const assessmentLevel = result.assessment_level || "easy";

  const readiness = result.readiness || {};
  const readinessScore = Number.isFinite(readiness.readiness_score)
    ? readiness.readiness_score
    : quizScore;
  const skillMatch = Number.isFinite(readiness.skill_match)
    ? readiness.skill_match
    : 0;
  const assessPerf = Number.isFinite(readiness.assessment_performance)
    ? readiness.assessment_performance
    : quizScore;
  const readinessLabel = readiness.label || "";
  const weakSubTopics = Array.isArray(result.weak_sub_topics)
    ? result.weak_sub_topics
    : [];
  const weakAreas = Array.isArray(result.weak_areas) ? result.weak_areas : [];
  const resources = Array.isArray(result.resources) ? result.resources : [];
  const executionResults = Array.isArray(result.execution_results)
    ? result.execution_results
    : [];
  const programmingLanguage = result.programming_language || "";

  // API-quality scores: use real values when available, null otherwise (null = model gets no signal)
  const readinessScoreForAPI = Number.isFinite(readiness.readiness_score)
    ? readiness.readiness_score
    : null;
  const quizScoreForAPI = quizScore > 0 ? quizScore : null;

  // ── Colours ───────────────────────────────────────────────────────────────
  const quizColor =
    quizScore >= 80 ? "#34D399" : quizScore >= 50 ? "#FBBF24" : "#F87171";

  const readinessLabelClass =
    readinessLabel === "Job Ready"
      ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/25"
      : readinessLabel === "Developing"
        ? "text-amber-400  bg-amber-400/10  border-amber-400/25"
        : "text-rose-400   bg-rose-400/10   border-rose-400/25";

  const quizLabel =
    quizScore >= 80
      ? "Strong performance"
      : quizScore >= 50
        ? "Room to improve"
        : "Needs more practice";

  return (
    <div className="space-y-8 animate-slide-up">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="glass p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="section-label">Results</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">
              {domain} assessment
            </h2>
            <p className="mt-1.5 text-sm text-slate-400">
              Readiness = (0.6 × Skill Match) + (0.4 × Quiz Score)
            </p>
            <span className="mt-3 inline-flex rounded-full border border-slate-700 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              {assessmentLevel} level · {totalQuestions} question
              {totalQuestions !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="flex gap-3">
            <button onClick={onRetake} className="btn-ghost text-xs">
              Retake test
            </button>
            <button onClick={onNewSearch} className="btn-primary text-xs">
              New search
            </button>
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
            <span
              className={`rounded-full border px-4 py-1.5 text-xs font-semibold ${readinessLabelClass}`}
            >
              {readinessLabel}
            </span>
          )}
          <div className="w-full space-y-3">
            <MiniBar
              label="Skill Match ×0.6"
              value={skillMatch}
              color="bg-indigo-500"
            />
            <MiniBar
              label="Quiz Score  ×0.4"
              value={assessPerf}
              color="bg-violet-500"
            />
          </div>
        </div>
      </div>

      {assessmentLevel === "medium" && executionResults.length > 0 && (
        <div className="glass p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="section-label">Coding Results</p>
              <p className="mt-2 text-sm text-slate-400">
                {programmingLanguage
                  ? `${programmingLanguage} execution summary`
                  : "Execution summary"}{" "}
                for each challenge.
              </p>
            </div>
            <span className="rounded-full border border-slate-700 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              {programmingLanguage || "code"}
            </span>
          </div>

          <div className="mt-6 grid gap-3">
            {executionResults.map((item) => (
              <div
                key={item.question_id}
                className={`rounded-2xl border p-4 ${
                  item.passed
                    ? "border-emerald-500/20 bg-emerald-500/10"
                    : "border-rose-500/20 bg-rose-500/10"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {item.sub_topic}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {item.passed_tests}/{item.total_tests} test cases passed
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${
                      item.passed
                        ? "bg-emerald-500/20 text-emerald-300"
                        : "bg-rose-500/20 text-rose-300"
                    }`}
                  >
                    {item.passed ? "Pass" : "Fail"}
                  </span>
                </div>
                {item.error_message && (
                  <p className="mt-3 rounded-xl bg-slate-950/50 px-3 py-2 font-mono text-xs text-slate-300">
                    {item.error_message}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Feedback + Weak sub-topics ──────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Feedback */}
        <div className="glass flex flex-col p-8 gap-6">
          <div>
            <p className="section-label">Feedback</p>
            <p className="mt-3 text-lg font-semibold text-white leading-snug">
              {result.feedback || "No feedback available."}
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
              <p className="text-sm text-emerald-300">
                No critical weak sub-topics detected.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── Dynamic Market Rate Intelligence ───────────────────────────────── */}
      <MarketRateCard
        domain={domain}
        experienceLevel={experienceLevel}
        skills={skills}
        token={token}
        readinessScore={readinessScoreForAPI}
        quizScore={quizScoreForAPI}
      />

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
                  <p className="text-[10px] uppercase tracking-wider text-indigo-400 mb-1">
                    {r.skill}
                  </p>
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
