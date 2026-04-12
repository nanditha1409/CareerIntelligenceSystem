import React, { useState, useEffect, useRef } from 'react';

const STEPS = [
  {
    number: '01',
    title: 'Skill Profiling',
    tag: 'Input Layer',
    color: 'indigo',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
      </svg>
    ),
    headline: 'Weighted skill vector',
    body: 'You rate each skill from 1 (Beginner) to 5 (Expert). The system builds a proficiency-weighted feature vector — not just a binary "have it / don\'t" — so a Python expert contributes 5× more signal than a Python beginner.',
    detail: 'Skill Match Score = Σ (proficiency / 5) for all matched domain skills',
    detailType: 'formula',
  },
  {
    number: '02',
    title: 'AI Recommendation',
    tag: 'ML Model',
    color: 'violet',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
    headline: 'Gradient Boosting Classifier',
    body: 'Your vector is fed into a Gradient Boosting Classifier trained on 540 labelled career profiles across 9 domains. The model outputs a probability distribution — the top 3 domains by confidence are returned as your matches.',
    detail: '91% cross-validated accuracy · 9 career classes · 32 skill features',
    detailType: 'stat',
  },
  {
    number: '03',
    title: 'Dynamic Assessment',
    tag: 'LLM Engine',
    color: 'purple',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
    headline: 'Personalised question generation',
    body: 'Gemini receives your exact proficiency map and generates 10 questions calibrated to your level. Skills rated 1–2 get conceptual fundamentals; skills rated 4–5 get scenario-based architectural challenges. Results are cached per session.',
    detail: 'Prompt: "Generate 10 MCQs for [Domain]. User proficiencies: [Skill Map]. Scale difficulty accordingly."',
    detailType: 'prompt',
  },
  {
    number: '04',
    title: 'Readiness Analytics',
    tag: 'Scoring',
    color: 'emerald',
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
      </svg>
    ),
    headline: 'Composite readiness formula',
    body: 'Your final score blends two signals: how well your skills cover the domain (weighted 60%) and how you performed on the tailored quiz (weighted 40%). Weak sub-topics are flagged for targeted study.',
    detail: 'Readiness = (0.6 × Skill Match) + (0.4 × Quiz Score)',
    detailType: 'formula',
  },
];

const COLOR_MAP = {
  indigo:  { ring: 'ring-indigo-500/30',  bg: 'bg-indigo-500/15',  border: 'border-indigo-500/30',  text: 'text-indigo-400',  bar: 'bg-indigo-500',  tag: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20' },
  violet:  { ring: 'ring-violet-500/30',  bg: 'bg-violet-500/15',  border: 'border-violet-500/30',  text: 'text-violet-400',  bar: 'bg-violet-500',  tag: 'bg-violet-500/10 text-violet-300 border-violet-500/20' },
  purple:  { ring: 'ring-purple-500/30',  bg: 'bg-purple-500/15',  border: 'border-purple-500/30',  text: 'text-purple-400',  bar: 'bg-purple-500',  tag: 'bg-purple-500/10 text-purple-300 border-purple-500/20' },
  emerald: { ring: 'ring-emerald-500/30', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', text: 'text-emerald-400', bar: 'bg-emerald-500', tag: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' },
};

// Animate on scroll into view
function useInView(threshold = 0.15) {
  const ref  = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, visible];
}

const StepCard = ({ step, index, active, onClick }) => {
  const c = COLOR_MAP[step.color];
  const [ref, visible] = useInView();

  return (
    <div
      ref={ref}
      onClick={onClick}
      style={{ transitionDelay: `${index * 80}ms` }}
      className={`cursor-pointer rounded-3xl border p-6 transition-all duration-500
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}
        ${active
          ? `${c.border} bg-slate-900/80 ring-1 ${c.ring} shadow-lg`
          : 'border-white/[0.07] bg-slate-900/40 hover:border-white/[0.12]'
        }`}
    >
      {/* Top row */}
      <div className="flex items-start justify-between mb-4">
        <div className={`flex h-11 w-11 items-center justify-center rounded-2xl border ${c.border} ${c.bg} ${c.text}`}>
          {step.icon}
        </div>
        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold ${c.tag}`}>
          {step.tag}
        </span>
      </div>

      {/* Step number + title */}
      <p className={`text-[11px] font-bold tracking-widest mb-1 ${c.text}`}>{step.number}</p>
      <h3 className="text-base font-semibold text-white mb-2">{step.title}</h3>
      <p className="text-xs text-slate-500 leading-relaxed">{step.headline}</p>

      {/* Expand indicator */}
      <div className={`mt-4 flex items-center gap-1.5 text-[10px] font-medium transition-colors ${active ? c.text : 'text-slate-600'}`}>
        <span>{active ? 'Hide detail' : 'Show detail'}</span>
        <svg className={`h-3 w-3 transition-transform duration-300 ${active ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </div>

      {/* Expanded detail */}
      <div className={`overflow-hidden transition-all duration-500 ${active ? 'max-h-64 mt-4' : 'max-h-0'}`}>
        <div className={`rounded-2xl border ${c.border} ${c.bg} p-4`}>
          <p className="text-xs text-slate-300 leading-relaxed mb-3">{step.body}</p>
          {step.detailType === 'formula' && (
            <code className={`block text-xs font-mono ${c.text} bg-slate-950/60 rounded-xl px-3 py-2`}>
              {step.detail}
            </code>
          )}
          {step.detailType === 'stat' && (
            <div className="flex flex-wrap gap-2">
              {step.detail.split('·').map((s, i) => (
                <span key={i} className={`rounded-full border px-2.5 py-1 text-[10px] font-medium ${c.tag}`}>
                  {s.trim()}
                </span>
              ))}
            </div>
          )}
          {step.detailType === 'prompt' && (
            <blockquote className={`border-l-2 ${c.bar} pl-3 text-[11px] italic text-slate-400`}>
              {step.detail}
            </blockquote>
          )}
        </div>
      </div>
    </div>
  );
};

const HowItWorks = () => {
  const [active, setActive] = useState(0);
  const [sectionRef, visible] = useInView(0.1);

  return (
    <section id="how-it-works" ref={sectionRef} className="py-20">
      {/* Heading */}
      <div className={`text-center mb-12 transition-all duration-700 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
        <p className="section-label mb-3">Under the hood</p>
        <h2 className="text-3xl font-bold text-white sm:text-4xl">How it works</h2>
        <p className="mt-3 text-slate-500 max-w-md mx-auto text-sm">
          Four stages — from raw skill input to a personalised readiness score.
        </p>
      </div>

      {/* Progress bar */}
      <div className="flex items-center justify-center gap-2 mb-10">
        {STEPS.map((s, i) => (
          <React.Fragment key={i}>
            <button
              onClick={() => setActive(i)}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i === active ? 'w-8 bg-indigo-500' : i < active ? 'w-4 bg-indigo-500/40' : 'w-4 bg-slate-700'
              }`}
            />
            {i < STEPS.length - 1 && <div className={`h-px w-6 transition-colors duration-300 ${i < active ? 'bg-indigo-500/40' : 'bg-slate-800'}`} />}
          </React.Fragment>
        ))}
      </div>

      {/* Cards grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step, i) => (
          <StepCard
            key={i}
            step={step}
            index={i}
            active={active === i}
            onClick={() => setActive(active === i ? -1 : i)}
          />
        ))}
      </div>
    </section>
  );
};

export default HowItWorks;
