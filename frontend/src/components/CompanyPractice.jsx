import React, { useEffect, useMemo, useState } from 'react';
import companyQuestions from '../config/companyQuestions';
import companyHRQuestions from "../config/companyHRQuestions.js";

const LEVELS = ['All', 'Easy', 'Medium', 'Hard'];

const LEVEL_STYLE = {
  Easy: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-300',
  Medium: 'border-amber-500/25 bg-amber-500/10 text-amber-300',
  Hard: 'border-rose-500/25 bg-rose-500/10 text-rose-300',
};

const CompanyPractice = ({ onBack }) => {
  const [selectedCompany, setSelectedCompany] = useState('Amazon');
  console.log(companyHRQuestions);
  const [mode, setMode] = useState('coding');
  const [difficulty, setDifficulty] = useState('All');
  const [search, setSearch] = useState('');

  const data = mode === 'coding' ? companyQuestions : companyHRQuestions;
  const selectedCompanyData = data.find(
    (c) => c.company === selectedCompany
  );

  const questions = selectedCompanyData?.questions || [];

  useEffect(() => {
    if (!selectedCompanyData && data[0]?.company) {
      setSelectedCompany(data[0].company);
    }
  }, [data, selectedCompanyData]);

  useEffect(() => {
    // Temporary debug logs for company-question mapping.
  
    console.log('Selected Company:', selectedCompany);
    console.log('Matched Data:', selectedCompanyData);
  }, [selectedCompany, selectedCompanyData]);

  const filteredQuestions = useMemo(() => {
    const term = search.trim().toLowerCase();
    return questions.filter((question) => {
      const label = (question.title || question.question || '').toLowerCase();
      const matchesDifficulty = mode === 'hr' || difficulty === 'All' || question.difficulty === difficulty;
      const matchesSearch = !term || label.includes(term);
      return matchesDifficulty && matchesSearch;
    });
  }, [difficulty, mode, search, questions]);

  return (
    <div className="space-y-8 animate-slide-up">
      <div className="glass p-8">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="section-label">Company Practice</p>
            <h2 className="mt-2 text-3xl font-semibold text-white">Company-wise coding question bank</h2>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Switch between coding and HR practice and browse company-wise question banks without any API calls.
            </p>
          </div>
          <button onClick={onBack} className="btn-ghost text-xs">Back to dashboard</button>
        </div>

        <div className="mt-6 space-y-4">
          <div>
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Mode</span>
            <div className="flex flex-wrap gap-2">
              {['coding', 'hr'].map((item) => (
                <button
                  key={item}
                  onClick={() => setMode(item)}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition-all ${
                    mode === item
                      ? 'bg-indigo-600 text-white shadow-glow-sm'
                      : 'border border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-white'
                  }`}
                >
                  {item === 'coding' ? 'Coding' : 'HR'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Company</span>
            <div className="flex flex-wrap gap-2">
              {data.map((c) => (
                <button
                  key={c.company}
                  onClick={() => setSelectedCompany(c.company)}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition-all ${
                    selectedCompany === c.company
                      ? 'bg-indigo-600 text-white shadow-glow-sm'
                      : 'border border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-white'
                  }`}
                >
                  {c.company}
                </button>
              ))}
            </div>
          </div>

          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Search title</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="input-base"
              placeholder="Search questions..."
            />
          </label>
        </div>

        {mode === 'coding' && (
          <div className="mt-5 flex flex-wrap items-center gap-2">
            {LEVELS.map((item) => (
              <button
                key={item}
                onClick={() => setDifficulty(item)}
                className={`rounded-full px-4 py-2 text-xs font-semibold transition-all ${
                  difficulty === item
                    ? 'bg-indigo-600 text-white shadow-glow-sm'
                    : 'border border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-white'
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="glass p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="section-label">{selectedCompanyData?.company || selectedCompany}</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">
              {filteredQuestions.length} questions available
            </h3>
          </div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
            {mode === 'coding' ? 'Open links in new tab' : 'Interview-ready answers'}
          </p>
        </div>
      </div>

      {filteredQuestions.length === 0 ? (
        <div className="glass p-10 text-center text-sm text-slate-400">
          No questions match this filter. Try another difficulty or clear search.
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredQuestions.map((question, index) => (
            <div
              key={`${question.title || question.question}-${index}`}
              className="rounded-3xl border border-white/[0.07] bg-slate-900/60 p-5 transition-all hover:border-indigo-500/35 hover:bg-indigo-500/5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-start gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-xs font-bold text-indigo-300">
                    {index + 1}
                  </span>
                  <div>
                    <h4 className="text-sm font-semibold text-white">{question.title || question.question}</h4>
                    {mode === 'coding' ? (
                      <a
                        href={question.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 block text-xs text-slate-500 hover:text-cyan-300"
                      >
                        {question.link}
                      </a>
                    ) : (
                      <p className="mt-2 text-sm leading-relaxed text-slate-400">{question.answer}</p>
                    )}
                  </div>
                </div>
                {mode === 'coding' && (
                  <span className={`rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.16em] ${LEVEL_STYLE[question.difficulty] || LEVEL_STYLE.Medium}`}>
                    {question.difficulty}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CompanyPractice;
