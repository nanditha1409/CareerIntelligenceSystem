import React, { useState } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const AuthPage = ({ onAuthSuccess, onBack }) => {
  const [mode, setMode] = useState('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const isSignIn = mode === 'signin';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    const endpoint = isSignIn ? '/api/auth/login' : '/api/auth/register';
    const body = isSignIn
      ? { email: email, password: password }
      : { email: email, password: password, full_name: fullName };

    try {
      // Fix: Ensure all authentication API calls send data in proper JSON format.
      // Explicitly matching the requested field names: email, password, full_name.
      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        // Safe error handling: Handle 400 / 401 responses with meaningful messages.
        if (res.status === 401) {
          throw new Error('Invalid email or password.');
        } else if (res.status === 400) {
          throw new Error(data.detail || 'Bad request. Please check your input.');
        } else {
          throw new Error(data.detail || 'Authentication failed.');
        }
      }

      onAuthSuccess?.(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 backdrop-blur-xl shadow-2xl shadow-indigo-900/20">
        <div className="mb-7">
          <p className="section-label">Private Career Cockpit</p>
          <h2 className="mt-2 text-3xl font-semibold text-white">
            {isSignIn ? 'Sign in to continue' : 'Create your account'}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Secure access to your recommendations, assessments, and AI guidance.
          </p>
        </div>

        <div className="mb-6 grid grid-cols-2 rounded-2xl border border-white/10 bg-slate-900/60 p-1">
          <button
            onClick={() => setMode('signin')}
            className={`rounded-xl px-4 py-2 text-sm transition-all duration-200 ${
              isSignIn ? 'bg-indigo-500/20 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setMode('signup')}
            className={`rounded-xl px-4 py-2 text-sm transition-all duration-200 ${
              !isSignIn ? 'bg-indigo-500/20 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Create Account
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {!isSignIn && (
            <div>
              <label className="mb-1.5 block text-xs uppercase tracking-wide text-slate-500">Full Name</label>
              <input
                className="input-base py-3"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ada Lovelace"
                required
              />
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-slate-500">Email</label>
            <input
              className="input-base py-3"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs uppercase tracking-wide text-slate-500">Password</label>
            <input
              className="input-base py-3"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              minLength={8}
              required
            />
          </div>

          {error && (
            <p className="rounded-2xl border border-rose-500/25 bg-rose-500/10 px-4 py-2.5 text-sm text-rose-300">
              {error}
            </p>
          )}

          <button className="btn-primary w-full" type="submit" disabled={submitting}>
            {submitting ? 'Please wait…' : isSignIn ? 'Sign In' : 'Create Account'}
          </button>

          <button type="button" onClick={onBack} className="btn-ghost w-full text-xs">
            Back to home
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;
