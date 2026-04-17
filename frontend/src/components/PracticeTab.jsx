import React, { useEffect, useMemo, useState } from 'react';
import companyQuestions from '../config/companyQuestions';

// Addition: small helper to keep the resource-style source label consistent without changing shared styling.
const getSourceLabel = (link) => {
  if (link.includes('leetcode.com')) return 'LeetCode';
  if (link.includes('geeksforgeeks.org')) return 'GeeksforGeeks';
  if (link.includes('hackerrank.com')) return 'HackerRank';
  return 'Practice Link';
};

// Addition: localStorage key for solved-question persistence across refreshes.
const SOLVED_STORAGE_KEY = 'solvedQuestions';

// Addition: filter labels are kept static so the Practice controls stay predictable and minimal.
const DIFFICULTY_FILTERS = ['All', 'Easy', 'Medium', 'Hard'];

// Addition: rule-based skill groups prioritize question themes without introducing backend or AI changes.
const SKILL_PRIORITY_GROUPS = [
  {
    matches: ['python', 'dsa', 'java', 'c++', 'c', 'go'],
    keywords: ['array', 'subarray', 'sum', 'stock', 'matrix', 'window', 'duplicate', 'paths', 'median', 'sort'],
  },
  {
    matches: ['ml', 'ai', 'tensorflow', 'pytorch'],
    keywords: ['median', 'sum', 'probability', 'target', 'dp', 'sequence', 'substrings', 'palindromic'],
  },
  {
    matches: ['html', 'css', 'js', 'javascript', 'typescript', 'react', 'node'],
    keywords: ['string', 'substring', 'anagram', 'parentheses', 'word', 'cache', 'graph'],
  },
];

// Addition: safe solved-question loader keeps the new state isolated and resilient to malformed storage.
const loadSolvedQuestions = () => {
  try {
    return JSON.parse(localStorage.getItem(SOLVED_STORAGE_KEY) || '{}');
  } catch {
    return {};
  }
};

// Addition: small ranking helper scores a question title against the current skill profile.
const getPracticePriorityScore = (title, skills) => {
  const normalizedTitle = title.toLowerCase();
  const skillNames = Object.keys(skills || {}).map((skill) => String(skill).toLowerCase());

  return SKILL_PRIORITY_GROUPS.reduce((score, group) => {
    const hasMatchingSkill = group.matches.some((skill) => skillNames.includes(skill));
    if (!hasMatchingSkill) return score;

    const keywordHits = group.keywords.filter((keyword) => normalizedTitle.includes(keyword)).length;
    return score + keywordHits;
  }, 0);
};

// Addition: dedicated Practice dashboard view that reuses the existing resource-card visual pattern.
const PracticeTab = ({ onBack, currentSkills = {} }) => {
  // Addition: selected company state ensures only one company is visible at a time.
  const [selectedCompany, setSelectedCompany] = useState(companyQuestions[0]?.company || '');
  // Addition: selected difficulty state powers the new All/Easy/Medium/Hard filter row.
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  // Addition: solved-question state persists checkmarks locally without affecting other dashboard features.
  const [solvedQuestions, setSolvedQuestions] = useState(() => loadSolvedQuestions());

  useEffect(() => {
    // Addition: reset scroll so the new dashboard page opens from the top like the other views.
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  useEffect(() => {
    // Addition: keep solved-question progress persistent across refreshes.
    localStorage.setItem(SOLVED_STORAGE_KEY, JSON.stringify(solvedQuestions));
  }, [solvedQuestions]);

  // Addition: derive the currently visible company block from selector state.
  const selectedCompanyBlock = useMemo(
    () => companyQuestions.find((companyBlock) => companyBlock.company === selectedCompany) || companyQuestions[0],
    [selectedCompany],
  );

  // Addition: apply skill-based prioritization first, then the difficulty filter, while keeping the original card grid.
  const visibleQuestions = useMemo(() => {
    if (!selectedCompanyBlock) return [];

    const sortedQuestions = [...selectedCompanyBlock.questions].sort((left, right) => {
      const rightScore = getPracticePriorityScore(right.title, currentSkills);
      const leftScore = getPracticePriorityScore(left.title, currentSkills);
      if (rightScore !== leftScore) return rightScore - leftScore;
      return left.title.localeCompare(right.title);
    });

    if (selectedDifficulty === 'All') {
      return sortedQuestions;
    }

    return sortedQuestions.filter((question) => question.difficulty === selectedDifficulty);
  }, [currentSkills, selectedCompanyBlock, selectedDifficulty]);

  // Addition: toggle helper updates solved state using the requested title-based storage structure.
  const handleSolvedToggle = (title) => {
    setSolvedQuestions((previous) => ({
      ...previous,
      [title]: !previous[title],
    }));
  };

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Addition: Practice page header, aligned with the existing recommendations/results headers. */}
      <div className="glass p-8">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="section-label">Practice</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">Company-wise coding questions</h2>
            <p className="mt-1.5 text-sm text-slate-400 max-w-2xl">
              Direct practice links grouped by company so you can prepare using familiar coding interview patterns.
            </p>
          </div>
          <button onClick={onBack} className="btn-ghost text-xs shrink-0">Back to home</button>
        </div>

        {/* Addition: company selector and difficulty filters reuse existing form/button styles without changing page layout. */}
        <div className="mt-6 flex flex-col gap-4">
          <div className="flex flex-col gap-2 sm:max-w-xs">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Company</p>
            <select
              value={selectedCompany}
              onChange={(event) => setSelectedCompany(event.target.value)}
              className="input-base py-3"
            >
              {companyQuestions.map((companyBlock) => (
                <option key={companyBlock.company} value={companyBlock.company}>
                  {companyBlock.company}
                </option>
              ))}
            </select>
          </div>

          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Difficulty</p>
            <div className="flex flex-wrap gap-2">
              {DIFFICULTY_FILTERS.map((difficulty) => (
                <button
                  key={difficulty}
                  onClick={() => setSelectedDifficulty(difficulty)}
                  className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-200 ${
                    selectedDifficulty === difficulty
                      ? 'bg-indigo-600 text-white shadow-glow-sm'
                      : 'border border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-white'
                  }`}
                >
                  {difficulty}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Addition: only the currently selected company is rendered, matching the requested one-company-at-a-time behavior. */}
      {selectedCompanyBlock && (
        <div key={selectedCompanyBlock.company} className="glass p-8">
          <div className="mb-5">
            <p className="section-label">Practice Set</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">{selectedCompanyBlock.company}</h3>
            <p className="mt-1 text-sm text-slate-500">
              {visibleQuestions.length} question{visibleQuestions.length !== 1 ? 's' : ''} shown
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {visibleQuestions.map((question) => {
              const isSolved = Boolean(solvedQuestions[question.title]);

              return (
                <div
                  key={`${selectedCompanyBlock.company}-${question.title}`}
                  className={`group flex items-start gap-3 rounded-2xl border bg-slate-950/50 p-4
                             transition-all duration-200 hover:border-indigo-500/40 hover:bg-indigo-500/5 ${
                               isSolved ? 'border-emerald-500/30 opacity-80' : 'border-slate-700/60'
                             }`}
                >
                  <label className="mt-0.5 flex items-center">
                    {/* Addition: solved checkbox persists per question title in localStorage. */}
                    <input
                      type="checkbox"
                      checked={isSolved}
                      onChange={() => handleSolvedToggle(question.title)}
                      className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-indigo-500 focus:ring-indigo-500/30"
                    />
                  </label>

                  <a
                    href={question.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex min-w-0 flex-1 items-start gap-3"
                  >
                    <span className="mt-0.5 text-base shrink-0">↗</span>
                    <div className="min-w-0">
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <p className="text-[10px] uppercase tracking-wider text-indigo-400">
                          {getSourceLabel(question.link)}
                        </p>
                        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] font-medium text-slate-400">
                          {question.difficulty}
                        </span>
                        {isSolved && (
                          <span className="rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
                            Solved
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-200 leading-snug group-hover:text-white transition-colors">
                        {question.title}
                      </p>
                    </div>
                  </a>
                </div>
              );
            })}
          </div>

          {/* Addition: empty-state messaging keeps the layout stable when a difficulty filter has no matches. */}
          {visibleQuestions.length === 0 && (
            <div className="mt-4 rounded-2xl border border-dashed border-slate-700/60 bg-slate-900/30 px-4 py-6 text-center">
              <p className="text-sm text-slate-400">No questions found for the selected difficulty.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PracticeTab;
