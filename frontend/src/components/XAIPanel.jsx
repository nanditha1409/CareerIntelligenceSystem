import React from 'react';

const XAIPanel = ({ recommendations = [] }) => {
  if (!recommendations.length) return null;

  return (
    <div className="glass p-8 animate-slide-up animation-delay-200">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <p className="section-label">Explainable AI</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Why these recommendations?</h2>
          <p className="mt-1.5 text-sm text-slate-400">
            Top skills that most influenced the model's prediction for each domain.
          </p>
        </div>
        <div className="shrink-0 flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-500/15 border border-indigo-500/25">
          <svg className="h-5 w-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15M14.25 3.104c.251.023.501.05.75.082M19.8 15l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.607L5 14.5m14.8.5l-1.57.393M5 14.5l-1.57.393" />
          </svg>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {recommendations.map((rec, idx) => (
          <div key={idx} className="rounded-2xl border border-white/[0.06] bg-slate-950/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20 text-xs font-bold text-indigo-300">
                {idx + 1}
              </span>
              <p className="text-sm font-semibold text-white">{rec.domain}</p>
            </div>
            {rec.fit_summary && (
              <p className="mb-4 text-xs leading-relaxed text-slate-300">
                {rec.fit_summary}
              </p>
            )}
            <ul className="space-y-2.5">
              {(rec.top_skills || []).map((insight, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                  <span className="mt-0.5 text-indigo-500 shrink-0">→</span>
                  <span>{insight}</span>
                </li>
              ))}
              {(!rec.top_skills || rec.top_skills.length === 0) && (
                <li className="text-xs text-slate-600">No strong skill signals detected.</li>
              )}
            </ul>
            {rec.project_suggestions?.length > 0 && (
              <div className="mt-4 rounded-2xl border border-indigo-500/10 bg-indigo-500/5 p-3">
                <p className="mb-2 text-[10px] uppercase tracking-[0.18em] text-indigo-300">Best proof project</p>
                <p className="text-xs leading-relaxed text-slate-300">{rec.project_suggestions[0]}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default XAIPanel;
