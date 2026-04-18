import React, { useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const INITIAL_FORM = {
  name: '',
  email: '',
  password: '',
};

const AuthScreen = ({ onAuthSuccess, theme = 'dark', onToggleTheme }) => {
  const [mode, setMode] = useState('signup');
  const [form, setForm] = useState(INITIAL_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const updateField = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setError('');
    setForm(INITIAL_FORM);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    const endpoint = mode === 'signup' ? '/auth/signup' : '/auth/login';
    const payload = mode === 'signup'
      ? {
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password,
        }
      : {
          email: form.email.trim(),
          password: form.password,
        };

    try {
      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed.');
      }

      onAuthSuccess(data.user);
      setForm(INITIAL_FORM);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`theme-${theme} relative min-h-screen overflow-hidden bg-slate-950 text-slate-100 transition-colors duration-300`}>
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-10%] top-[-8%] h-80 w-80 rounded-full bg-cyan-500/12 blur-[120px]" />
        <div className="absolute right-[-5%] top-[20%] h-[28rem] w-[28rem] rounded-full bg-indigo-500/14 blur-[140px]" />
        <div className="absolute bottom-[-8%] left-[30%] h-72 w-72 rounded-full bg-emerald-500/10 blur-[120px]" />
      </div>

      <div className="relative mx-auto grid min-h-screen max-w-7xl items-center gap-12 px-6 py-10 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
        <button
          type="button"
          onClick={onToggleTheme}
          className="absolute right-6 top-6 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-200 backdrop-blur-xl transition-colors hover:bg-white/10"
        >
          {theme === 'dark' ? 'Light' : 'Dark'} mode
        </button>

        <section className="space-y-8">
          <div className="inline-flex items-center gap-3 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
            Personalized career intelligence
          </div>

          <div className="max-w-2xl space-y-5">
            <h1 className="text-5xl font-black leading-[0.95] tracking-tight text-white sm:text-6xl lg:text-7xl">
              Build your
              <span className="block bg-gradient-to-r from-cyan-300 via-sky-300 to-indigo-300 bg-clip-text text-transparent">
                private career cockpit
              </span>
            </h1>
            <p className="max-w-xl text-lg leading-relaxed text-slate-300">
              Create an account to save recommendations, track every assessment, and unlock a personal dashboard built around your progress.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ['Persistent history', 'Every skill analysis and test attempt linked to your account.'],
              ['Smarter retakes', 'Next rounds can focus on the topics you missed most.'],
              ['Personal dashboard', 'A single place to monitor growth, readiness, and next steps.'],
            ].map(([title, text]) => (
              <div key={title} className="rounded-3xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl">
                <p className="text-sm font-semibold text-white">{title}</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{text}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="glass noise relative mx-auto w-full max-w-md p-8">
          <div className="mb-6 flex rounded-full border border-white/10 bg-slate-900/70 p-1">
            {[
              ['signup', 'Create account'],
              ['login', 'Sign in'],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => switchMode(value)}
                className={`flex-1 rounded-full px-4 py-2.5 text-sm font-semibold transition-all duration-200 ${
                  mode === value
                    ? 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-white shadow-glow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white">
              {mode === 'signup' ? 'Start your workspace' : 'Welcome back'}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              {mode === 'signup'
                ? 'Sign up once and we’ll start building your personal recommendation history immediately.'
                : 'Log in to continue from your saved analyses and assessments.'}
            </p>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {mode === 'signup' && (
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                  Full name
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={updateField('name')}
                  className="input-base"
                  placeholder="Career explorer"
                  autoComplete="name"
                  required
                />
              </div>
            )}

            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Email
              </label>
              <input
                type="email"
                value={form.email}
                onChange={updateField('email')}
                className="input-base"
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Password
              </label>
              <input
                type="password"
                value={form.password}
                onChange={updateField('password')}
                className="input-base"
                placeholder={mode === 'signup' ? 'Minimum 6 characters' : 'Enter your password'}
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                required
              />
            </div>

            {error && (
              <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                {error}
              </div>
            )}

            <button type="submit" disabled={isSubmitting} className="inline-flex w-full items-center justify-center rounded-2xl bg-gradient-to-r from-cyan-500 to-indigo-500 px-6 py-3.5 text-sm font-semibold text-white transition-transform duration-200 hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100">
              {isSubmitting
                ? (mode === 'signup' ? 'Creating account…' : 'Signing in…')
                : (mode === 'signup' ? 'Create account' : 'Sign in')}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
};

export default AuthScreen;
