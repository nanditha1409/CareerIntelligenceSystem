import React from 'react';

const Navbar = () => {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/95 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4 lg:px-8">
        <div>
          <p className="text-lg font-semibold text-white">CareerBloom</p>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">AI talent intelligence</p>
        </div>
        <nav className="hidden items-center gap-8 text-sm text-slate-400 md:flex">
          <button className="transition hover:text-white">Why us</button>
          <button className="transition hover:text-white">How it works</button>
          <button className="transition hover:text-white">Results</button>
        </nav>
        <button className="rounded-full bg-indigo-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-400">
          Launch analysis
        </button>
      </div>
    </header>
  );
};

export default Navbar;
