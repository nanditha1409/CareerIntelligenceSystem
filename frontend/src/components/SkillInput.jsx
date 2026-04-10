import React from 'react';

const SkillInput = ({ onAnalyze, isLoading }) => {
  const [skills, setSkills] = React.useState('');

  const handleSubmit = () => {
    const skillArray = skills.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
    onAnalyze(skillArray);
  };

  return (
    <div className="rounded-[2rem] border border-white/10 bg-slate-900/95 p-6 shadow-2xl shadow-slate-950/20 ring-1 ring-white/5">
      <label className="block text-sm font-semibold text-slate-200 mb-3">Your skills</label>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <input
          className="w-full rounded-2xl border border-slate-700 bg-slate-950/90 px-4 py-3 text-slate-100 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
          type="text"
          placeholder="e.g. python, sql, ml"
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
        />
        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="inline-flex shrink-0 items-center justify-center rounded-full bg-indigo-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
        >
          {isLoading ? 'Analyzing…' : 'Analyze Skills'}
        </button>
      </div>
      <p className="mt-3 text-sm text-slate-500">Separate skills with commas, then get tailored career recommendations and test options.</p>
    </div>
  );
};

export default SkillInput;
