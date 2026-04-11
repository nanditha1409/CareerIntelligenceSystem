import React, { useState } from 'react';
import RadarChart from './RadarChart';

const TYPE_ICON = { video: '▶', course: '🎓', article: '📄' };

const SkillGapPanel = ({ skillGap = [], resources = [], allSkills = [] }) => {
  const [activeIdx, setActiveIdx] = useState(0);
  if (!skillGap.length) return null;

  const active = skillGap[activeIdx];

  // Build radar data for the active domain
  // Use up to 8 skills from the domain master set
  const radarSkills = [...(active.matched_skills || []), ...(active.missing_skills || [])].slice(0, 8);
  const userVals   = radarSkills.map((s) => (active.matched_skills?.includes(s) ? 1 : 0));
  const domainVals = radarSkills.map(() => 1);

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Header */}
      <div className="glass p-8">
        <p className="section-label">Skill Gap Analysis</p>
        <h2 className="mt-2 text-2xl font-semibold text-white">What to learn next</h2>
        <p className="mt-1.5 text-sm text-slate-400 max-w-xl">
          Your skills compared against each domain's master set. The radar shows coverage at a glance.
        </p>

        {/* Domain tabs */}
        <div className="mt-5 flex flex-wrap gap-2">
          {skillGap.map((gap, i) => (
            <button
              key={i}
              onClick={() => setActiveIdx(i)}
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-200 ${
                activeIdx === i
                  ? 'bg-indigo-600 text-white shadow-glow-sm'
                  : 'border border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-white'
              }`}
            >
              {gap.domain}
            </button>
          ))}
        </div>
      </div>

      {/* Main panel */}
      <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
        {/* Radar */}
        <div className="glass flex flex-col items-center justify-center gap-4 p-8">
          <RadarChart
            labels={radarSkills}
            userValues={userVals}
            domainValues={domainVals}
            size={240}
          />
          {/* Legend */}
          <div className="flex items-center gap-5 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-4 rounded-full bg-violet-500" />
              Your skills
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-4 rounded-full border border-indigo-500/60 border-dashed" />
              Domain target
            </span>
          </div>
        </div>

        {/* Gap details */}
        <div className="glass p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">{active.domain}</h3>
            <span className="rounded-full bg-indigo-500/15 border border-indigo-500/25 px-3 py-1 text-xs font-semibold text-indigo-300">
              {active.match_percentage}% covered
            </span>
          </div>

          {/* Progress bar */}
          <div>
            <div className="h-2 w-full rounded-full bg-slate-800">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700"
                style={{ width: `${active.match_percentage}%` }}
              />
            </div>
          </div>

          {/* Matched */}
          {active.matched_skills?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Skills you have ✓</p>
              <div className="flex flex-wrap gap-2">
                {active.matched_skills.map((s) => (
                  <span key={s} className="rounded-full bg-emerald-500/10 border border-emerald-500/25 px-3 py-1 text-xs font-medium text-emerald-300">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Missing */}
          {active.missing_skills?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Skills to learn</p>
              <div className="flex flex-wrap gap-2">
                {active.missing_skills.map((s) => (
                  <span key={s} className="rounded-full bg-rose-500/10 border border-rose-500/25 px-3 py-1 text-xs font-medium text-rose-300">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Resources */}
      {resources.length > 0 && (
        <div className="glass p-8">
          <p className="section-label mb-4">Learning Resources</p>
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
                <span className="mt-0.5 text-base shrink-0">{TYPE_ICON[r.type] || '📄'}</span>
                <div className="min-w-0">
                  <p className="text-[10px] uppercase tracking-wider text-indigo-400 mb-1">{r.skill}</p>
                  <p className="text-sm font-medium text-slate-200 leading-snug group-hover:text-white transition-colors">
                    {r.title}
                  </p>
                  <p className="mt-1 text-[10px] text-slate-600 capitalize">{r.type}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillGapPanel;
