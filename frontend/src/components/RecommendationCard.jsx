import React from 'react';

const RecommendationCard = ({ recommendation, onTakeTest }) => {
  return (
    <div className="group rounded-[2rem] border border-white/10 bg-slate-900/90 p-6 shadow-xl shadow-slate-950/20 transition hover:-translate-y-1 hover:border-indigo-500/20 hover:bg-slate-900">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h3 className="text-xl font-semibold text-white">{recommendation.domain}</h3>
        <span className="rounded-full bg-indigo-500/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-indigo-200">Top pick</span>
      </div>
      <div className="grid gap-3 text-sm text-slate-400">
        <div className="rounded-3xl bg-slate-950/80 p-4">
          <p className="text-slate-300">Confidence</p>
          <p className="mt-2 text-lg font-semibold text-white">{recommendation.confidence}%</p>
        </div>
        <div className="rounded-3xl bg-slate-950/80 p-4">
          <p className="text-slate-300">Salary</p>
          <p className="mt-2 text-lg font-semibold text-white">{recommendation.salary}</p>
        </div>
        <div className="rounded-3xl bg-slate-950/80 p-4">
          <p className="text-slate-300">Demand</p>
          <p className="mt-2 text-lg font-semibold text-white">{recommendation.demand}</p>
        </div>
      </div>
      <div className="mt-6 text-sm text-slate-300">
        <p className="font-medium text-slate-100">Why this?</p>
        <ul className="mt-3 space-y-2 text-slate-400">
          {recommendation.reason.map((r, i) => (
            <li key={i} className="rounded-2xl bg-slate-950/80 px-3 py-2">{r}</li>
          ))}
        </ul>
      </div>
      <button
        onClick={() => onTakeTest(recommendation.domain)}
        className="mt-7 inline-flex w-full items-center justify-center rounded-full bg-indigo-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400"
      >
        Take the domain test
      </button>
    </div>
  );
};

export default RecommendationCard;
