import React from 'react';

const DEMAND_COLOR = {
  'High':      'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  'Medium':    'text-amber-400  bg-amber-400/10  border-amber-400/20',
  'Low':       'text-rose-400 bg-rose-400/10 border-rose-400/20',
};

const RANK_LABEL = ['#1 Match', '#2 Match', '#3 Match'];

const RecommendationCard = ({ recommendation, onTakeTest, rank = 0 }) => {
  const demandLevel = recommendation.demand?.level || 'Medium';
  const demandPct = recommendation.demand?.percentage || 0;
  const demandClass = DEMAND_COLOR[demandLevel] || DEMAND_COLOR['Medium'];
  const isTop = rank === 0;

  return (
    <div
      className={`group relative flex flex-col rounded-3xl border transition-all duration-300
        hover:-translate-y-1 hover:shadow-glow-sm
        ${isTop
          ? 'border-indigo-500/40 bg-gradient-to-b from-indigo-950/60 to-slate-900/80 shadow-glow-sm'
          : 'border-white/[0.07] bg-slate-900/60 hover:border-indigo-500/20'
        } backdrop-blur-sm`}
    >
      {/* Top accent bar */}
      {isTop && (
        <div className="absolute inset-x-0 top-0 h-px rounded-t-3xl bg-gradient-to-r from-transparent via-indigo-500/60 to-transparent" />
      )}

      <div className="flex flex-col gap-5 p-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <span className="section-label">{RANK_LABEL[rank] || `#${rank + 1} Match`}</span>
            <h3 className="mt-1.5 text-lg font-semibold text-white leading-snug">{recommendation.role}</h3>
          </div>
        </div>

        {/* Confidence bar */}
        <div>
          <div className="flex justify-between text-xs mb-1.5">
            <span className="text-slate-500">Confidence match</span>
            <span className="font-semibold text-white">{recommendation.confidence}%</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-slate-800">
            <div
              className="h-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700"
              style={{ width: `${recommendation.confidence}%` }}
            />
          </div>
        </div>

        {/* Stats row */}
        <div className="rounded-2xl border border-white/[0.06] bg-slate-950/60 p-5 space-y-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Recommended Role</p>
            <p className="text-base font-semibold text-white leading-tight">{recommendation.role}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Market Demand</p>
            <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold tracking-wide ${demandClass}`}>
              {demandLevel} ({demandPct}%)
            </span>
          </div>
        </div>

        {/* Why this */}
        {recommendation.reason?.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Why this domain</p>
            <div className="flex flex-wrap gap-1.5">
              {recommendation.reason.slice(0, 4).map((r, i) => (
                <span key={i} className="skill-tag">{r}</span>
              ))}
            </div>
          </div>
        )}

        {recommendation.fit_summary && (
          <div className="rounded-2xl border border-cyan-500/15 bg-cyan-500/5 p-4">
            <p className="text-[10px] uppercase tracking-wider text-cyan-300 mb-2">Why this role fits you</p>
            <p className="text-sm leading-relaxed text-slate-300">{recommendation.fit_summary}</p>
          </div>
        )}

        {recommendation.growth_summary && (
          <div className="rounded-2xl bg-slate-950/60 p-4">
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">What would strengthen the fit</p>
            <p className="text-sm leading-relaxed text-slate-400">{recommendation.growth_summary}</p>
          </div>
        )}

        {recommendation.missing_priority_skills?.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Priority skills to close</p>
            <div className="flex flex-wrap gap-2">
              {recommendation.missing_priority_skills.map((skill) => (
                <span key={skill} className="rounded-full bg-rose-500/10 border border-rose-500/25 px-3 py-1 text-xs font-medium text-rose-300">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {recommendation.project_suggestions?.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Portfolio ideas for you</p>
            <div className="space-y-2">
              {recommendation.project_suggestions.slice(0, 2).map((project, index) => (
                <div key={index} className="rounded-2xl border border-white/[0.05] bg-slate-950/60 px-4 py-3">
                  <p className="text-sm leading-relaxed text-slate-300">{project}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* CTA */}
      <div className="mt-auto p-6 pt-0">
        <button
          onClick={() => onTakeTest(recommendation.role)}
          className={`w-full rounded-2xl py-3 text-sm font-semibold transition-all duration-200
            ${isTop
              ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover:from-indigo-500 hover:to-violet-500 hover:scale-[1.02] shadow-glow-sm'
              : 'border border-slate-700 text-slate-300 hover:border-indigo-500/50 hover:text-white hover:bg-indigo-500/5'
            }`}
        >
          Take domain test →
        </button>
      </div>
    </div>
  );
};

export default RecommendationCard;
