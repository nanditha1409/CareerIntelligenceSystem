import React, { useState, useRef } from 'react';

const SUGGESTIONS = ['python', 'react', 'sql', 'docker', 'ml', 'typescript', 'aws', 'figma', 'node', 'kubernetes'];

const SkillInput = ({ onAnalyze, isLoading }) => {
  const [input, setInput] = useState('');
  const [tags, setTags] = useState([]);
  const [focused, setFocused] = useState(false);
  const inputRef = useRef(null);

  const addTag = (skill) => {
    const s = skill.trim().toLowerCase();
    if (s && !tags.includes(s)) setTags((prev) => [...prev, s]);
    setInput('');
    inputRef.current?.focus();
  };

  const removeTag = (skill) => setTags((prev) => prev.filter((t) => t !== skill));

  const handleKeyDown = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
      e.preventDefault();
      addTag(input);
    }
    if (e.key === 'Backspace' && !input && tags.length) {
      setTags((prev) => prev.slice(0, -1));
    }
  };

  const handleSubmit = () => {
    const all = input.trim()
      ? [...tags, ...input.split(',').map((s) => s.trim()).filter(Boolean)]
      : tags;
    if (all.length) onAnalyze(all);
  };

  const unusedSuggestions = SUGGESTIONS.filter((s) => !tags.includes(s));

  return (
    <div className="mx-auto max-w-2xl animate-slide-up">
      {/* Glass search bar */}
      <div
        className={`relative rounded-3xl border transition-all duration-300 ${
          focused
            ? 'border-indigo-500/60 bg-slate-900/80 shadow-glow-indigo ring-2 ring-indigo-500/20'
            : 'border-slate-700/60 bg-slate-900/50 shadow-card'
        } backdrop-blur-xl p-4`}
        onClick={() => inputRef.current?.focus()}
      >
        {/* Tags + input row */}
        <div className="flex flex-wrap items-center gap-2 min-h-[2.5rem]">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 px-3 py-1 text-xs font-medium text-indigo-300"
            >
              {tag}
              <button
                onClick={(e) => { e.stopPropagation(); removeTag(tag); }}
                className="ml-0.5 rounded-full text-indigo-400 hover:text-white transition-colors"
                aria-label={`Remove ${tag}`}
              >
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder={tags.length === 0 ? 'Type a skill and press Enter — e.g. python, react, sql…' : 'Add more skills…'}
            className="flex-1 min-w-[180px] bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none"
          />
        </div>

        {/* Divider + action row */}
        <div className="mt-3 flex items-center justify-between border-t border-slate-700/50 pt-3">
          <p className="text-xs text-slate-500">
            {tags.length > 0 ? `${tags.length} skill${tags.length > 1 ? 's' : ''} added` : 'Press Enter or comma to add each skill'}
          </p>
          <button
            onClick={handleSubmit}
            disabled={isLoading || (tags.length === 0 && !input.trim())}
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
            <button
              key={s}
              onClick={() => addTag(s)}
              className="skill-tag cursor-pointer"
            >
              + {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default SkillInput;
