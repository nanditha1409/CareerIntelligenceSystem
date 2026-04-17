import React, { useEffect, useState } from 'react';

const NAV_ITEMS = [
  { label: 'How it works', id: 'how-it-works' },
  { label: 'Domains',      id: 'domains' },
  { label: 'Results',      id: 'results' },
];

const Navbar = ({ onLaunch, onNavClick, onPracticeClick, isPracticeActive, user, onAuthClick, onLogout }) => {
  const [scrolled, setScrolled]   = useState(false);
  const [active, setActive]       = useState('');
  const [menuOpen, setMenuOpen]   = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 12);
      // Highlight active section based on scroll position
      for (const item of [...NAV_ITEMS].reverse()) {
        const el = document.getElementById(item.id);
        if (el && window.scrollY >= el.offsetTop - 120) {
          setActive(item.id);
          return;
        }
      }
      setActive('');
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollTo = (id) => {
    setMenuOpen(false);
    // If a parent handler is provided (e.g. to switch to HOME view first), call it
    if (onNavClick) onNavClick(id);
    // Small delay so view switch can render the section before scrolling
    setTimeout(() => {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
  };

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'border-b border-white/[0.06] bg-slate-950/80 backdrop-blur-xl shadow-[0_1px_0_rgba(255,255,255,0.04)]'
          : 'bg-transparent'
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4 lg:px-8">

        {/* Logo */}
        <button
          onClick={() => scrollTo('how-it-works') || window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="flex items-center gap-3"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-glow-sm">
            <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
          </div>
          <div className="text-left">
            <p className="text-sm font-bold tracking-tight text-white">CareerBloom</p>
            <p className="text-[10px] uppercase tracking-[0.25em] text-slate-500 leading-none">AI Intelligence</p>
          </div>
        </button>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map(({ label, id }) => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className={`rounded-full px-4 py-2 text-sm transition-all duration-150 ${
                active === id
                  ? 'bg-indigo-500/15 text-white font-medium'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
              }`}
            >
              {label}
            </button>
          ))}
          {/* Addition: Practice tab entry reuses the existing nav button styling without changing layout structure. */}
          <button
            onClick={onPracticeClick}
            className={`rounded-full px-4 py-2 text-sm transition-all duration-150 ${
              isPracticeActive
                ? 'bg-indigo-500/15 text-white font-medium'
                : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
            }`}
          >
            Practice
          </button>
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {user ? (
            <div className="hidden sm:flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span>{user.full_name}</span>
            </div>
          ) : (
            <button onClick={onAuthClick} className="btn-ghost text-xs px-4 py-2">
              Sign In
            </button>
          )}

          <button onClick={onLaunch} className="btn-primary text-xs px-4 py-2">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
            </svg>
            Launch analysis
          </button>
          {user && (
            <button onClick={onLogout} className="btn-ghost text-xs px-4 py-2 hidden sm:inline-flex">
              Logout
            </button>
          )}

          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="md:hidden flex h-8 w-8 items-center justify-center rounded-xl border border-slate-700 text-slate-400"
            aria-label="Toggle menu"
          >
            {menuOpen ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-white/[0.06] bg-slate-950/95 backdrop-blur-xl px-6 py-4 space-y-1">
          {/* Addition: mobile Practice entry mirrors the existing mobile nav item pattern. */}
          <button
            onClick={() => {
              setMenuOpen(false);
              if (onPracticeClick) onPracticeClick();
            }}
            className={`block w-full text-left rounded-2xl px-4 py-3 text-sm transition-colors ${
              isPracticeActive ? 'bg-indigo-500/15 text-white' : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            Practice
          </button>
          {NAV_ITEMS.map(({ label, id }) => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className={`block w-full text-left rounded-2xl px-4 py-3 text-sm transition-colors ${
                active === id ? 'bg-indigo-500/15 text-white' : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
};

export default Navbar;
