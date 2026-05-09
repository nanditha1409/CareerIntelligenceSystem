import React from 'react';

const ResumeSummaryPanel = ({
  filename,
  yearsOfExperience,
  domainScores,
  semanticMatches,
  onDismiss,
}) => {
  // Use domainScores if available, fall back to semanticMatches, cap at 3
  const scores = (domainScores?.length ? domainScores : semanticMatches || []).slice(0, 3);

  return (
    <div className="animate-fade-in rounded-2xl border border-slate-700/60 bg-slate-900/50 backdrop-blur-xl p-5 relative">
      {/* Dismiss */}
      <button
        onClick={onDismiss}
        aria-label="Dismiss resume panel"
        className="absolute top-4 right-4 text-slate-500 hover:text-slate-200 transition-colors"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Header */}
      <div className="flex items-center gap-2.5 pr-6">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-500/15 border border-emerald-500/30">
          <svg className="h-3.5 w-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </span>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-white leading-tight">Resume parsed</p>
          {filename && (
            <p className="text-xs text-slate-500 truncate mt-0.5">{filename}</p>
          )}
        </div>
      </div>

      {/* Years of experience */}
      {yearsOfExperience != null && (
        <div className="mt-4 flex items-center gap-2 text-sm text-slate-300">
          <svg className="h-4 w-4 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>
            <span className="font-semibold text-white">{yearsOfExperience}</span>
            {' '}year{yearsOfExperience !== 1 ? 's' : ''} of experience detected
          </span>
        </div>
      )}

      {/* Semantic domain matches */}
      {scores.length > 0 && (
        <div className="mt-4">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2.5">
            Semantic domain matches
          </p>
          <div className="grid gap-2 sm:grid-cols-3">
            {scores.map((s, i) => {
              const pct = s.confidence_pct != null
                ? Math.round(s.confidence_pct)
                : s.similarity_score != null
                  ? (s.similarity_score <= 1 ? Math.round(s.similarity_score * 100) : Math.round(s.similarity_score))
                  : Math.round(s.confidence ?? 0);
              return (
                <div
                  key={i}
                  className="rounded-xl border border-slate-700/50 bg-slate-800/50 px-3 py-2.5"
                >
                  <p className="text-xs font-medium text-white leading-snug truncate">
                    {s.domain}
                  </p>
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="flex-1 h-1 rounded-full bg-slate-700">
                      <div
                        className="h-1 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-700"
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-semibold text-indigo-300 shrink-0">
                      {pct}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeSummaryPanel;
