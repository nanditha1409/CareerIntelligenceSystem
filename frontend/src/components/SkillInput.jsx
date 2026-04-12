import React, { useState, useRef } from 'react';

const SUGGESTIONS = ['python', 'react', 'sql', 'docker', 'ml', 'typescript', 'aws', 'figma', 'node', 'kubernetes'];

const PROFICIENCY_LABELS = {
  1: 'Beginner',
  2: 'Elementary',
  3: 'Intermediate',
  4: 'Advanced',
  5: 'Expert',
};

const PROFICIENCY_COLORS = {
  1: 'bg-rose-500/20 border-rose-500/40 text-rose-300',
  2: 'bg-orange-500/20 border-orange-500/40 text-orange-300',
  3: 'bg-amber-500/20 border-amber-500/40 text-amber-300',
  4: 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300',
  5: 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300',
};

// ── Skill chip with proficiency selector ─────────────────────────────────────
const SkillChip = ({ skill, level, onChange, onRemove }) => (
  <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${PROFICIENCY_COLORS[level]}`}>
    {skill}
    {/* Proficiency stepper */}
    <button
      onClick={(e) => { e.stopPropagation(); onChange(Math.max(1, level - 1)); }}
      className="opacity-60 hover:opacity-100 transition-opacity leading-none"
      aria-label="Decrease proficiency"
    >−</button>
    <span className="font-bold w-3 text-center">{level}</span>
    <button
      onClick={(e) => { e.stopPropagation(); onChange(Math.min(5, level + 1)); }}
      className="opacity-60 hover:opacity-100 transition-opacity leading-none"
      aria-label="Increase proficiency"
    >+</button>
    <span className="opacity-50 text-[9px] hidden sm:inline">{PROFICIENCY_LABELS[level]}</span>
    <button
      onClick={(e) => { e.stopPropagation(); onRemove(); }}
      className="ml-0.5 opacity-60 hover:opacity-100 transition-opacity"
      aria-label={`Remove ${skill}`}
    >
      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </span>
);

// ── Main ──────────────────────────────────────────────────────────────────────
const SkillInput = ({ onAnalyze, isLoading }) => {
  // skills: { [skillName]: proficiency (1-5) }
  const [skills, setSkills]   = useState({});
  const [input, setInput]     = useState('');
  const [focused, setFocused] = useState(false);
  const inputRef = useRef(null);

  const addSkill = (name) => {
    const s = name.trim().toLowerCase();
    if (s && !(s in skills)) {
      setSkills((prev) => ({ ...prev, [s]: 3 })); // default: Intermediate
    }
    setInput('');
    inputRef.current?.focus();
  };

  const removeSkill = (name) =>
    setSkills((prev) => { const n = { ...prev }; delete n[name]; return n; });

  const updateLevel = (name, level) =>
    setSkills((prev) => ({ ...prev, [name]: level }));

  const handleKeyDown = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
      e.preventDefault();
      addSkill(input);
    }
    if (e.key === 'Backspace' && !input) {
      const keys = Object.keys(skills);
      if (keys.length) removeSkill(keys[keys.length - 1]);
    }
  };

  const handleSubmit = () => {
    const pending = input.trim();
    const final   = pending ? { ...skills, [pending.toLowerCase()]: 3 } : skills;
    if (Object.keys(final).length) onAnalyze(final);
  };

  const skillCount       = Object.keys(skills).length;
  const unusedSuggestions = SUGGESTIONS.filter((s) => !(s in skills));

  return (
    <div className="mx-auto max-w-2xl animate-slide-up">
      <div
        className={`relative rounded-3xl border transition-all duration-300 ${
          focused
            ? 'border-indigo-500/60 bg-slate-900/80 shadow-glow-indigo ring-2 ring-indigo-500/20'
            : 'border-slate-700/60 bg-slate-900/50 shadow-card'
        } backdrop-blur-xl p-4`}
        onClick={() => inputRef.current?.focus()}
      >
        {/* Chips + input */}
        <div className="flex flex-wrap items-center gap-2 min-h-[2.5rem]">
          {Object.entries(skills).map(([skill, level]) => (
            <SkillChip
              key={skill}
              skill={skill}
              level={level}
              onChange={(l) => updateLevel(skill, l)}
              onRemove={() => removeSkill(skill)}
            />
          ))}
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder={skillCount === 0 ? 'Type a skill and press Enter — e.g. python, react, sql…' : 'Add more skills…'}
            className="flex-1 min-w-[180px] bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none"
          />
        </div>

        {/* Proficiency legend */}
        {skillCount > 0 && (
          <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-slate-600">
            {Object.entries(PROFICIENCY_LABELS).map(([n, label]) => (
              <span key={n} className="flex items-center gap-1">
                <span className="font-bold text-slate-400">{n}</span> = {label}
              </span>
            ))}
            <span className="text-slate-600">· use +/− on each chip to adjust</span>
          </div>
        )}

        {/* Action row */}
        <div className="mt-3 flex items-center justify-between border-t border-slate-700/50 pt-3">
          <p className="text-xs text-slate-500">
            {skillCount > 0
              ? `${skillCount} skill${skillCount > 1 ? 's' : ''} · questions adapt to your proficiency levels`
              : 'Press Enter or comma to add each skill'}
          </p>
          <button
            onClick={handleSubmit}
            disabled={isLoading || (skillCount === 0 && !input.trim())}
            className="btn-primary text-xs px-5 py-2.5"
          >
            {isLoading ? (
              <>
                <svg className="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Analyzing…
              </>
            ) : (
              <>
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
                Analyze Skills
              </>
            )}
          </button>
        </div>
      </div>

      {/* Quick-add suggestions */}
      {unusedSuggestions.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 animate-fade-in">
          <span className="text-xs text-slate-600">Quick add:</span>
          {unusedSuggestions.slice(0, 7).map((s) => (
            <button key={s} onClick={() => addSkill(s)} className="skill-tag cursor-pointer">
              + {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default SkillInput;
