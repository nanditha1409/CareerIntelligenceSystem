import React from 'react';
import ProgressRing from './ProgressRing';

const formatDate = (value) => {
  if (!value) return 'Recently';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Recently';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
};

const EmptyState = ({ onStartAnalysis }) => (
  <div className="glass p-8 text-center">
    <p className="section-label">Dashboard</p>
    <h2 className="mt-2 text-3xl font-semibold text-white">Your journey starts here</h2>
    <p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-400">
      Run your first skill analysis to start building recommendation history, readiness tracking, and a personalized roadmap.
    </p>
    <button onClick={onStartAnalysis} className="btn-primary mt-6 text-sm">
      Launch first analysis
    </button>
  </div>
);

const TimelineCard = ({ title, items, renderMeta, renderBody, emptyLabel }) => (
  <div className="glass p-8">
    <p className="section-label">{title}</p>
    {items.length === 0 ? (
      <p className="mt-4 text-sm text-slate-500">{emptyLabel}</p>
    ) : (
      <div className="mt-5 space-y-4">
        {items.map((item) => (
          <div key={item.id} className="rounded-3xl border border-white/[0.06] bg-slate-950/50 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              {renderMeta(item)}
              <span className="text-xs text-slate-500">{formatDate(item.created_at)}</span>
            </div>
            <div className="mt-4">{renderBody(item)}</div>
          </div>
        ))}
      </div>
    )}
  </div>
);

const JourneyDashboard = ({ currentUser, dashboardData, dashboardLoading, onStartAnalysis }) => {
  if (dashboardLoading) {
    return (
      <div className="glass flex items-center justify-center p-12">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-700 border-t-cyan-400" />
          <p className="mt-4 text-sm text-slate-400">Loading your dashboard…</p>
        </div>
      </div>
    );
  }

  const overview = dashboardData?.overview;
  const roadmap = dashboardData?.roadmap;
  const recommendationHistory = dashboardData?.recommendation_history || [];
  const assessmentHistory = dashboardData?.assessment_history || [];

  if (!overview || (overview.analyses_count === 0 && overview.assessments_count === 0)) {
    return <EmptyState onStartAnalysis={onStartAnalysis} />;
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="glass p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="section-label">Dashboard</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">{currentUser.name}, here’s your saved journey</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              This dashboard keeps your recommendation history, assessment progress, and a roadmap built from your latest skill snapshot.
            </p>
          </div>
          <button onClick={onStartAnalysis} className="btn-primary text-sm">
            Start a new analysis
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ['Analyses saved', overview.analyses_count],
            ['Assessments taken', overview.assessments_count],
            ['Latest top domain', overview.latest_top_domain || 'Not yet'],
            ['Average readiness', `${overview.average_readiness}%`],
          ].map(([label, value]) => (
            <div key={label} className="glass p-6">
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</p>
              <p className="mt-3 text-2xl font-bold text-white">{value}</p>
            </div>
          ))}
        </div>

        <div className="glass flex flex-col items-center justify-center gap-4 p-8">
          <p className="section-label self-start">Latest Readiness</p>
          <ProgressRing
            value={overview.latest_readiness || 0}
            size={150}
            strokeWidth={12}
            sublabel="latest score"
            color="#22c55e"
          />
          <p className="text-center text-sm text-slate-400">
            {overview.latest_top_domain
              ? `Most recent target: ${overview.latest_top_domain}`
              : 'Take an assessment to unlock readiness tracking.'}
          </p>
        </div>
      </div>

      {roadmap && (
        <div className="glass p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="section-label">Personalized Roadmap</p>
              <h3 className="mt-2 text-2xl font-semibold text-white">{roadmap.target_domain}</h3>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">{roadmap.summary}</p>
            </div>
            <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-4 py-2 text-xs font-semibold text-cyan-200">
              {roadmap.match_percentage}% matched
            </span>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="rounded-3xl border border-white/[0.06] bg-slate-950/50 p-6">
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Current strengths</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(roadmap.current_strengths || []).length > 0 ? roadmap.current_strengths.map((skill) => (
                  <span key={skill} className="rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
                    {skill}
                  </span>
                )) : <span className="text-sm text-slate-500">Build your first analysis to identify strengths.</span>}
              </div>
            </div>

            <div className="rounded-3xl border border-white/[0.06] bg-slate-950/50 p-6">
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Next skills to learn</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(roadmap.next_skills || []).length > 0 ? roadmap.next_skills.map((skill) => (
                  <span key={skill} className="rounded-full border border-rose-500/25 bg-rose-500/10 px-3 py-1 text-xs font-medium text-rose-300">
                    {skill}
                  </span>
                )) : <span className="text-sm text-slate-500">You already cover the core stack. Focus on projects and interview practice.</span>}
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="space-y-4">
              {(roadmap.weekly_plan || []).map((step) => (
                <div key={step.week} className="rounded-3xl border border-white/[0.06] bg-slate-950/50 p-6">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{step.title}</p>
                    <span className="rounded-full border border-indigo-500/25 bg-indigo-500/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-indigo-300">
                      Week {step.week}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-slate-400">{step.objective}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {(step.skills || []).map((skill) => (
                      <span key={skill} className="skill-tag">{skill}</span>
                    ))}
                  </div>
                  <p className="mt-4 text-xs text-slate-500">
                    Checkpoint: {step.checkpoint}
                  </p>
                </div>
              ))}
            </div>

            <div className="rounded-3xl border border-white/[0.06] bg-slate-950/50 p-6">
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Recommended resources</p>
              <div className="mt-4 space-y-3">
                {(roadmap.resources || []).map((resource, index) => (
                  <a
                    key={`${resource.skill}-${index}`}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-2xl border border-slate-700/60 bg-slate-900/60 p-4 transition-colors hover:border-cyan-500/40 hover:bg-cyan-500/5"
                  >
                    <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">{resource.skill}</p>
                    <p className="mt-1 text-sm font-medium text-white">{resource.title}</p>
                    <p className="mt-1 text-[10px] uppercase tracking-[0.18em] text-slate-500">{resource.type}</p>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <TimelineCard
          title="Recommendation History"
          items={recommendationHistory}
          emptyLabel="No recommendation history yet."
          renderMeta={(item) => (
            <div>
              <p className="text-sm font-semibold text-white">{item.top_domain}</p>
              <p className="mt-1 text-xs text-slate-500">{item.confidence}% confidence</p>
            </div>
          )}
          renderBody={(item) => (
            <div className="flex flex-wrap gap-2">
              {item.skills_input.map((skill) => (
                <span key={skill} className="skill-tag">{skill}</span>
              ))}
            </div>
          )}
        />

        <TimelineCard
          title="Assessment History"
          items={assessmentHistory}
          emptyLabel="No assessments completed yet."
          renderMeta={(item) => (
            <div>
              <p className="text-sm font-semibold text-white">{item.domain}</p>
              <p className="mt-1 text-xs text-slate-500">Readiness {item.readiness_score}%</p>
            </div>
          )}
          renderBody={(item) => (
            <div className="grid grid-cols-3 gap-3">
              {[
                ['Quiz', `${item.assessment_score}%`],
                ['Skill match', `${item.skill_match}%`],
                ['Readiness', `${item.readiness_score}%`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl bg-slate-900/80 p-3">
                  <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
                  <p className="mt-2 text-sm font-semibold text-white">{value}</p>
                </div>
              ))}
            </div>
          )}
        />
      </div>
    </div>
  );
};

export default JourneyDashboard;
