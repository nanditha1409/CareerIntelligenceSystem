import React, { useState, useRef } from 'react';
import Navbar from './components/Navbar';
import SkillInput from './components/SkillInput';
import RecommendationCard from './components/RecommendationCard';
import TestSection from './components/TestSection';
import ResultDashboard from './components/ResultDashboard';
import SkillGapPanel from './components/SkillGapPanel';
import XAIPanel from './components/XAIPanel';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const VIEW = { HOME: 'home', RECS: 'recs', TEST: 'test', RESULTS: 'results' };

const STATS = [
  { value: '9+',   label: 'Career domains' },
  { value: '32',   label: 'Skills tracked' },
  { value: '91%',  label: 'Model accuracy' },
  { value: '540',  label: 'Training samples' },
];

export default function App() {
  const [view, setView]                   = useState(VIEW.HOME);
  const [isLoading, setIsLoading]         = useState(false);
  const [error, setError]                 = useState(null);
  const [currentSkills, setCurrentSkills] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [skillGap, setSkillGap]           = useState([]);
  const [resources, setResources]         = useState([]);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [testResult, setTestResult]       = useState(null);
  const inputRef = useRef(null);

  const handleAnalyze = async (skillArray) => {
    setError(null);
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/recommend-career`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skills: skillArray }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to get recommendations');
      }
      const data = await res.json();
      setCurrentSkills(skillArray);
      setRecommendations(data.recommendations || []);
      setSkillGap(data.skill_gap || []);
      setResources(data.resources || []);
      setView(VIEW.RECS);
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTakeTest = (domain) => { setSelectedDomain(domain); setTestResult(null); setView(VIEW.TEST); };
  const handleTestComplete = (result) => { setTestResult(result); setView(VIEW.RESULTS); };
  const handleRetake = () => { setTestResult(null); setView(VIEW.TEST); };
  const handleNewSearch = () => {
    setRecommendations([]); setSkillGap([]); setResources([]);
    setTestResult(null); setSelectedDomain(''); setCurrentSkills([]);
    setView(VIEW.HOME);
  };

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden">

      {/* Background glow blobs */}
      <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-[600px] w-[900px] rounded-full bg-indigo-600/10 blur-[120px]" />
        <div className="absolute top-1/3 -right-40 h-[400px] w-[600px] rounded-full bg-violet-600/8 blur-[100px]" />
        <div className="absolute bottom-0 -left-40 h-[400px] w-[600px] rounded-full bg-indigo-800/8 blur-[100px]" />
      </div>

      <Navbar onLaunch={() => { handleNewSearch(); setTimeout(() => inputRef.current?.focus(), 100); }} />

      <main className="relative mx-auto max-w-6xl px-6 py-12 lg:px-8">

        {/* Error banner */}
        {error && (
          <div className="mb-8 flex items-center justify-between rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-300 animate-fade-in">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-4 text-rose-400 hover:text-white transition-colors">✕</button>
          </div>
        )}

        {/* ── HOME ─────────────────────────────────────────────────────────── */}
        {view === VIEW.HOME && (
          <div className="space-y-16">
            {/* Hero */}
            <div className="text-center space-y-6 pt-8 pb-4 animate-fade-in">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-medium text-indigo-300">
                <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse-slow" />
                AI-powered career intelligence
              </div>

              <h1 className="text-5xl font-extrabold text-white leading-[1.1] tracking-tight sm:text-6xl lg:text-7xl">
                Find your ideal<br />
                <span className="gradient-text">career path</span>
              </h1>

              <p className="text-slate-400 max-w-lg mx-auto text-lg leading-relaxed">
                Enter your skills and get data-driven recommendations, skill gap analysis, and a personalised readiness score — in seconds.
              </p>
            </div>

            {/* Skill input */}
            <div ref={inputRef}>
              <SkillInput onAnalyze={handleAnalyze} isLoading={isLoading} />
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-slide-up animation-delay-300">
              {STATS.map(({ value, label }) => (
                <div key={label} className="glass flex flex-col items-center gap-1 py-5 px-4 text-center">
                  <span className="text-2xl font-bold gradient-text">{value}</span>
                  <span className="text-xs text-slate-500">{label}</span>
                </div>
              ))}
            </div>

            {/* Feature preview cards */}
            <div className="grid gap-5 sm:grid-cols-3 animate-slide-up animation-delay-400">
              {[
                {
                  icon: (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
                    </svg>
                  ),
                  title: 'Career Recommendations',
                  desc: 'Top 3 domain matches with confidence scores, salary ranges, and market demand.',
                },
                {
                  icon: (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ),
                  title: 'Skill Gap Analysis',
                  desc: 'Radar chart showing your coverage vs. domain requirements with curated resources.',
                },
                {
                  icon: (
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                  ),
                  title: 'Readiness Score',
                  desc: 'Weighted formula combining skill match (60%) and assessment performance (40%).',
                },
              ].map(({ icon, title, desc }) => (
                <div key={title} className="glass p-6 group hover:border-indigo-500/20 transition-all duration-300">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-500/15 border border-indigo-500/20 text-indigo-400 group-hover:bg-indigo-500/25 transition-colors">
                    {icon}
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-1.5">{title}</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── RECOMMENDATIONS ───────────────────────────────────────────────── */}
        {view === VIEW.RECS && (
          <div className="space-y-10">
            <div className="flex items-center justify-between animate-fade-in">
              <div>
                <p className="section-label">Recommendations</p>
                <h2 className="mt-2 text-3xl font-semibold text-white">Your top career matches</h2>
              </div>
              <button onClick={handleNewSearch} className="btn-ghost text-xs">New search</button>
            </div>

            <div className="grid gap-6 lg:grid-cols-3 animate-slide-up">
              {recommendations.map((rec, i) => (
                <RecommendationCard key={i} recommendation={rec} onTakeTest={handleTakeTest} rank={i} />
              ))}
            </div>

            <XAIPanel recommendations={recommendations} />
            <SkillGapPanel skillGap={skillGap} resources={resources} />
          </div>
        )}

        {/* ── TEST ─────────────────────────────────────────────────────────── */}
        {view === VIEW.TEST && (
          <TestSection
            domain={selectedDomain}
            skills={currentSkills}
            onComplete={handleTestComplete}
            onBack={() => setView(VIEW.RECS)}
          />
        )}

        {/* ── RESULTS ──────────────────────────────────────────────────────── */}
        {view === VIEW.RESULTS && (
          <ResultDashboard
            result={testResult}
            domain={selectedDomain}
            onRetake={handleRetake}
            onNewSearch={handleNewSearch}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="relative mt-24 border-t border-white/[0.05] py-8 text-center text-xs text-slate-600">
        CareerBloom — AI Career Intelligence · Built with FastAPI + React + Tailwind
      </footer>
    </div>
  );
}
