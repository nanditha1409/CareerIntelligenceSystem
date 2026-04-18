import React, { useEffect, useMemo, useRef, useState } from 'react';
import Navbar from './components/Navbar';
import ExperienceProfile from './components/ExperienceProfile';
import RecommendationCard from './components/RecommendationCard';
import TestSection from './components/TestSection';
import ResultDashboard from './components/ResultDashboard';
import SkillGapPanel from './components/SkillGapPanel';
import AuthScreen from './components/AuthScreen';
import JourneyDashboard from './components/JourneyDashboard';
import CompanyPractice from './components/CompanyPractice';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const AUTH_STORAGE_KEY = 'career-bloom-user';
const THEME_STORAGE_KEY = 'career-bloom-theme';
const VIEW = {
  DASHBOARD: 'dashboard',
  HOME: 'home',
  RECS: 'recs',
  TEST: 'test',
  RESULTS: 'results',
  COMPANY: 'company',
};

const STATS = [
  { value: '9+', label: 'Career domains' },
  { value: '35', label: 'Skills tracked' },
  { value: '91%', label: 'Model accuracy' },
  { value: '540', label: 'Training samples' },
];

const loadStoredUser = () => {
  if (typeof window === 'undefined') return null;

  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const loadStoredTheme = () => {
  if (typeof window === 'undefined') return 'dark';

  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  return stored === 'light' ? 'light' : 'dark';
};

export default function App() {
  const [view, setView] = useState(VIEW.DASHBOARD);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentSkills, setCurrentSkills] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [skillGap, setSkillGap] = useState([]);
  const [resources, setResources] = useState([]);
  const [selectedDomain, setSelectedDomain] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [currentUser, setCurrentUser] = useState(loadStoredUser);
  const [dashboardData, setDashboardData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [theme, setTheme] = useState(loadStoredTheme);
  const inputRef = useRef(null);

  const personalizedGreeting = useMemo(() => {
    if (!currentUser?.name) return 'Your career workspace';
    return `${currentUser.name.split(' ')[0]}'s career workspace`;
  }, [currentUser]);

  const persistUser = (user) => {
    setCurrentUser(user);
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
    setView(VIEW.DASHBOARD);
  };

  const toggleTheme = () => {
    setTheme((current) => {
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      return nextTheme;
    });
  };

  const handleLogout = () => {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    setCurrentUser(null);
    setRecommendations([]);
    setSkillGap([]);
    setResources([]);
    setTestResult(null);
    setSelectedDomain('');
    setCurrentSkills([]);
    setDashboardData(null);
    setView(VIEW.DASHBOARD);
    setError(null);
  };

  const loadDashboard = async (userId = currentUser?.user_id) => {
    if (!userId) return;

    setDashboardLoading(true);
    try {
      const res = await fetch(`${API}/users/${userId}/dashboard`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to load dashboard');
      }
      setDashboardData(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setDashboardLoading(false);
    }
  };

  const clearRecommendationHistory = async () => {
    if (!currentUser?.user_id) return;
    setError(null);
    try {
      const res = await fetch(`${API}/users/${currentUser.user_id}/history/recommendations`, {
        method: 'DELETE',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Failed to clear recommendation history');
      await loadDashboard(currentUser.user_id);
    } catch (e) {
      setError(e.message);
    }
  };

  const clearAssessmentHistory = async () => {
    if (!currentUser?.user_id) return;
    setError(null);
    try {
      const res = await fetch(`${API}/users/${currentUser.user_id}/history/assessments`, {
        method: 'DELETE',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Failed to clear assessment history');
      await loadDashboard(currentUser.user_id);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (!currentUser?.user_id) return;
    loadDashboard(currentUser.user_id);
  }, [currentUser?.user_id]);

  const handleAnalyze = async (exp, githubProjects) => {
    const skillArray = exp.skillsUsed;
    
    setError(null);
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/recommend-career`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skills: skillArray,
          user_id: currentUser?.user_id ?? null,
        }),
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
      if (currentUser?.user_id) {
        loadDashboard(currentUser.user_id);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTakeTest = (domain) => { setSelectedDomain(domain); setTestResult(null); setView(VIEW.TEST); };
  const handleTestComplete = (result) => {
    setTestResult(result);
    setView(VIEW.RESULTS);
    if (currentUser?.user_id) {
      loadDashboard(currentUser.user_id);
    }
  };
  const handleRetake = () => { setTestResult(null); setView(VIEW.TEST); };
  const handleNewSearch = () => {
    setRecommendations([]);
    setSkillGap([]);
    setResources([]);
    setTestResult(null);
    setSelectedDomain('');
    setCurrentSkills([]);
    setView(VIEW.HOME);
  };

  if (!currentUser) {
    return <AuthScreen onAuthSuccess={persistUser} theme={theme} onToggleTheme={toggleTheme} />;
  }

  return (
    <div className={`theme-${theme} relative min-h-screen overflow-x-hidden bg-slate-950 text-slate-100 transition-colors duration-300`}>
      <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-indigo-600/10 blur-[120px]" />
        <div className="absolute top-1/3 -right-40 h-[400px] w-[600px] rounded-full bg-violet-600/8 blur-[100px]" />
        <div className="absolute bottom-0 -left-40 h-[400px] w-[600px] rounded-full bg-indigo-800/8 blur-[100px]" />
      </div>

      <Navbar
        onLaunch={() => { handleNewSearch(); setTimeout(() => inputRef.current?.focus(), 100); }}
        currentUser={currentUser}
        onLogout={handleLogout}
        onDashboard={() => setView(VIEW.DASHBOARD)}
        onCompanyPractice={() => setView(VIEW.COMPANY)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main className="relative mx-auto max-w-6xl px-6 py-12 lg:px-8">
        {error && (
          <div className="mb-8 flex items-center justify-between rounded-2xl border border-rose-500/30 bg-rose-500/10 px-5 py-4 text-sm text-rose-300 animate-fade-in">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-4 text-rose-400 transition-colors hover:text-white">✕</button>
          </div>
        )}

        {view === VIEW.DASHBOARD && (
          <JourneyDashboard
            currentUser={currentUser}
            dashboardData={dashboardData}
            dashboardLoading={dashboardLoading}
            onStartAnalysis={() => {
              setView(VIEW.HOME);
              setTimeout(() => inputRef.current?.focus(), 100);
            }}
            onStartCompanyPractice={() => setView(VIEW.COMPANY)}
            onClearRecommendationHistory={clearRecommendationHistory}
            onClearAssessmentHistory={clearAssessmentHistory}
          />
        )}

        {view === VIEW.HOME && (
          <div className="space-y-16">
            <div className="space-y-6 pt-8 pb-4 text-center animate-fade-in">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-1.5 text-xs font-medium text-cyan-300">
                <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse-slow" />
                Signed in as {currentUser.email}
              </div>

              <h1 className="text-5xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-6xl lg:text-7xl">
                {personalizedGreeting}
                <span className="gradient-text block">Find your next role with context</span>
              </h1>

              <p className="mx-auto max-w-2xl text-lg leading-relaxed text-slate-400">
                Your account is ready. Start analyzing skills now, and every recommendation and assessment will be tied to your personal dashboard history.
              </p>
            </div>

            <div ref={inputRef}>
              <ExperienceProfile onAnalyze={handleAnalyze} isLoading={isLoading} currentUser={currentUser} />
            </div>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-slide-up animation-delay-300">
              {STATS.map(({ value, label }) => (
                <div key={label} className="glass flex flex-col items-center gap-1 px-4 py-5 text-center">
                  <span className="text-2xl font-bold gradient-text">{value}</span>
                  <span className="text-xs text-slate-500">{label}</span>
                </div>
              ))}
            </div>

            <div className="grid gap-5 sm:grid-cols-3 animate-slide-up animation-delay-400">
              {[
                {
                  title: 'Secure account access',
                  desc: 'Your recommendations and future dashboard history now live behind a sign-in.',
                },
                {
                  title: 'History-ready tracking',
                  desc: 'Every new skill analysis and domain test is already linked to your user profile.',
                },
                {
                  title: 'Dashboard foundation',
                  desc: 'Next we can surface saved runs, readiness trends, and retake progress in one place.',
                },
              ].map(({ title, desc }) => (
                <div key={title} className="glass p-6 transition-all duration-300 hover:border-cyan-500/20">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-2xl border border-cyan-500/20 bg-cyan-500/15 text-cyan-300">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12A9 9 0 1 1 3 12a9 9 0 0 1 18 0Z" />
                    </svg>
                  </div>
                  <h3 className="mb-1.5 text-sm font-semibold text-white">{title}</h3>
                  <p className="text-xs leading-relaxed text-slate-500">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {view === VIEW.COMPANY && (
          <CompanyPractice
            currentUser={currentUser}
            onBack={() => setView(VIEW.DASHBOARD)}
            onAttemptSaved={() => loadDashboard(currentUser.user_id)}
          />
        )}

        {view === VIEW.RECS && (
          <div className="space-y-10">
            <div className="flex items-center justify-between animate-fade-in">
              <div>
                <p className="section-label">Recommendations</p>
                <h2 className="mt-2 text-3xl font-semibold text-white">Your top career matches</h2>
                <p className="mt-2 text-sm text-slate-500">
                  Saved under {currentUser.name} so we can build your personal dashboard next.
                </p>
              </div>
              <button onClick={handleNewSearch} className="btn-ghost text-xs">New search</button>
            </div>

            <div className="grid gap-6 lg:grid-cols-3 animate-slide-up">
              {recommendations.map((rec, i) => (
                <RecommendationCard key={i} recommendation={rec} onTakeTest={handleTakeTest} rank={i} />
              ))}
            </div>

            <SkillGapPanel skillGap={skillGap} resources={resources} />
          </div>
        )}

        {view === VIEW.TEST && (
          <TestSection
            domain={selectedDomain}
            skills={currentSkills}
            currentUser={currentUser}
            onComplete={handleTestComplete}
            onBack={() => setView(VIEW.RECS)}
          />
        )}

        {view === VIEW.RESULTS && (
          <ResultDashboard
            result={testResult}
            domain={selectedDomain}
            onRetake={handleRetake}
            onNewSearch={handleNewSearch}
          />
        )}
      </main>

      <footer className="relative mt-24 border-t border-white/[0.05] py-8 text-center text-xs text-slate-600">
        CareerBloom — AI Career Intelligence · Built with FastAPI + React + Tailwind
      </footer>
    </div>
  );
}
