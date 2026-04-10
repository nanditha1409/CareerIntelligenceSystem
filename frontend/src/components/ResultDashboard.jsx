import React from 'react';

const ResultDashboard = ({ result, domain, onRetake, onNewSearch }) => {
  if (!result) return null;

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] border border-white/10 bg-slate-900/95 p-8 shadow-2xl shadow-slate-950/30">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-indigo-300">Results</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Your {domain} readiness score</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">Review feedback and use weak areas to guide your next steps.</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              onClick={onRetake}
              className="rounded-full border border-slate-700 bg-slate-900/90 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-indigo-500 hover:text-white"
            >
              Retake test
            </button>
            <button
              onClick={onNewSearch}
              className="rounded-full bg-indigo-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400"
            >
              New search
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-[2rem] border border-white/10 bg-slate-900/95 p-8 shadow-xl shadow-slate-950/20">
          <p className="text-sm uppercase tracking-[0.24em] text-indigo-300">Score</p>
          <p className="mt-4 text-5xl font-semibold text-white">{result.score}%</p>
          <p className="mt-3 text-sm leading-6 text-slate-400">Your readiness score is calculated from your test performance and domain fit.</p>
        </div>
        <div className="rounded-[2rem] border border-white/10 bg-slate-900/95 p-8 shadow-xl shadow-slate-950/20">
          <p className="text-sm uppercase tracking-[0.24em] text-indigo-300">Feedback</p>
          <p className="mt-4 text-lg font-semibold text-white">{result.feedback || 'No feedback available.'}</p>
          <p className="mt-3 text-sm leading-6 text-slate-400">Use this guidance to strengthen the skills that matter most.</p>
        </div>
        <div className="rounded-[2rem] border border-white/10 bg-slate-900/95 p-8 shadow-xl shadow-slate-950/20">
          <p className="text-sm uppercase tracking-[0.24em] text-indigo-300">Weak areas</p>
          {result.weak_areas && result.weak_areas.length > 0 ? (
            <ul className="mt-4 space-y-3 text-slate-300">
              {result.weak_areas.map((area, index) => (
                <li key={index} className="rounded-2xl bg-slate-950/90 px-4 py-3">{area}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 text-sm leading-6 text-slate-400">No major weaknesses detected.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultDashboard;
