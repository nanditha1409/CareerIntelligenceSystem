import React, { useState, useEffect, useRef } from 'react';

const DOMAINS = [
  {
    name: 'Data Scientist',
    emoji: '🔬',
    color: 'indigo',
    salary: '₹6–15 LPA',
    demand: 'High',
    desc: 'Extract insights from complex datasets using statistical modelling, machine learning, and visualisation to drive data-informed decisions.',
    skills: ['Machine Learning', 'Statistics', 'Python / Pandas'],
  },
  {
    name: 'AI-ML Engineer',
    emoji: '🤖',
    color: 'violet',
    salary: '₹10–18 LPA',
    demand: 'Very High',
    desc: 'Design, train, and deploy production-grade deep learning models — from transformer architectures to scalable inference pipelines.',
    skills: ['Deep Learning', 'MLOps / Docker', 'PyTorch / TensorFlow'],
  },
  {
    name: 'Data Analyst',
    emoji: '📊',
    color: 'blue',
    salary: '₹4–10 LPA',
    demand: 'High',
    desc: 'Transform raw data into actionable business intelligence through SQL queries, BI dashboards, and statistical analysis.',
    skills: ['SQL & Window Functions', 'Power BI / Tableau', 'Excel & DAX'],
  },
  {
    name: 'Full Stack Developer',
    emoji: '🌐',
    color: 'cyan',
    salary: '₹5–14 LPA',
    demand: 'Very High',
    desc: 'Build end-to-end web applications — from React frontends and REST/GraphQL APIs to database design and cloud deployment.',
    skills: ['React & TypeScript', 'Node.js / Express', 'Databases & APIs'],
  },
  {
    name: 'Software Engineer',
    emoji: '⚙️',
    color: 'amber',
    salary: '₹5–12 LPA',
    demand: 'High',
    desc: 'Architect robust, scalable software systems using strong fundamentals in data structures, algorithms, and design patterns.',
    skills: ['Data Structures & Algorithms', 'System Design', 'OOP & Testing'],
  },
  {
    name: 'DevOps Engineer',
    emoji: '🚀',
    color: 'orange',
    salary: '₹6–15 LPA',
    demand: 'High',
    desc: 'Automate infrastructure, build CI/CD pipelines, and manage containerised workloads to keep systems reliable and deployable.',
    skills: ['Docker & Kubernetes', 'CI/CD Pipelines', 'Terraform / IaC'],
  },
  {
    name: 'Cybersecurity Analyst',
    emoji: '🔐',
    color: 'rose',
    salary: '₹7–12 LPA',
    demand: 'High',
    desc: 'Protect systems and data by identifying vulnerabilities, responding to incidents, and implementing security frameworks.',
    skills: ['Network Security', 'Cryptography', 'Incident Response'],
  },
  {
    name: 'UI/UX Designer',
    emoji: '🎨',
    color: 'pink',
    salary: '₹4–10 LPA',
    demand: 'Medium',
    desc: 'Craft intuitive, accessible digital experiences through user research, interaction design, and high-fidelity prototyping in Figma.',
    skills: ['Wireframing & Prototyping', 'Visual Design', 'UX Research'],
  },
  {
    name: 'Backend Developer',
    emoji: '🗄️',
    color: 'teal',
    salary: '₹5–13 LPA',
    demand: 'High',
    desc: 'Build the server-side logic, APIs, and data layers that power applications — with a focus on performance, security, and scalability.',
    skills: ['REST API Design', 'Databases & Caching', 'Auth & Security'],
  },
];

const DEMAND_COLOR = {
  'Very High': 'text-emerald-400 bg-emerald-400/10 border-emerald-400/25',
  'High':      'text-indigo-400  bg-indigo-400/10  border-indigo-400/25',
  'Medium':    'text-amber-400   bg-amber-400/10   border-amber-400/25',
};

const COLOR_MAP = {
  indigo:  { border: 'hover:border-indigo-500/40',  icon: 'bg-indigo-500/15 border-indigo-500/30 text-indigo-300',  skill: 'bg-indigo-500/10 text-indigo-300',  btn: 'border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/15' },
  violet:  { border: 'hover:border-violet-500/40',  icon: 'bg-violet-500/15 border-violet-500/30 text-violet-300',  skill: 'bg-violet-500/10 text-violet-300',  btn: 'border-violet-500/40 text-violet-300 hover:bg-violet-500/15' },
  blue:    { border: 'hover:border-blue-500/40',    icon: 'bg-blue-500/15 border-blue-500/30 text-blue-300',        skill: 'bg-blue-500/10 text-blue-300',      btn: 'border-blue-500/40 text-blue-300 hover:bg-blue-500/15' },
  cyan:    { border: 'hover:border-cyan-500/40',    icon: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-300',        skill: 'bg-cyan-500/10 text-cyan-300',      btn: 'border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/15' },
  amber:   { border: 'hover:border-amber-500/40',   icon: 'bg-amber-500/15 border-amber-500/30 text-amber-300',     skill: 'bg-amber-500/10 text-amber-300',    btn: 'border-amber-500/40 text-amber-300 hover:bg-amber-500/15' },
  orange:  { border: 'hover:border-orange-500/40',  icon: 'bg-orange-500/15 border-orange-500/30 text-orange-300',  skill: 'bg-orange-500/10 text-orange-300',  btn: 'border-orange-500/40 text-orange-300 hover:bg-orange-500/15' },
  rose:    { border: 'hover:border-rose-500/40',    icon: 'bg-rose-500/15 border-rose-500/30 text-rose-300',        skill: 'bg-rose-500/10 text-rose-300',      btn: 'border-rose-500/40 text-rose-300 hover:bg-rose-500/15' },
  pink:    { border: 'hover:border-pink-500/40',    icon: 'bg-pink-500/15 border-pink-500/30 text-pink-300',        skill: 'bg-pink-500/10 text-pink-300',      btn: 'border-pink-500/40 text-pink-300 hover:bg-pink-500/15' },
  teal:    { border: 'hover:border-teal-500/40',    icon: 'bg-teal-500/15 border-teal-500/30 text-teal-300',        skill: 'bg-teal-500/10 text-teal-300',      btn: 'border-teal-500/40 text-teal-300 hover:bg-teal-500/15' },
};

function useInView(threshold = 0.1) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, visible];
}

const DomainCard = ({ domain, index, onTakeTest }) => {
  const c = COLOR_MAP[domain.color];
  const [ref, visible] = useInView(0.08);

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${(index % 3) * 70}ms` }}
      className={`group flex flex-col rounded-3xl border border-white/[0.07] bg-slate-900/50 p-6
        backdrop-blur-sm transition-all duration-500 ${c.border}
        hover:bg-slate-900/70 hover:shadow-lg hover:-translate-y-0.5
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className={`flex h-12 w-12 items-center justify-center rounded-2xl border text-2xl ${c.icon}`}>
          {domain.emoji}
        </div>
        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold ${DEMAND_COLOR[domain.demand]}`}>
          {domain.demand} demand
        </span>
      </div>

      {/* Title + salary */}
      <h3 className="text-sm font-bold text-white mb-0.5">{domain.name}</h3>
      <p className="text-[11px] text-slate-500 mb-3">{domain.salary}</p>

      {/* Description */}
      <p className="text-xs text-slate-400 leading-relaxed flex-1 mb-4">{domain.desc}</p>

      {/* Core skills */}
      <div className="mb-5">
        <p className="text-[10px] uppercase tracking-wider text-slate-600 mb-2">Core skills</p>
        <div className="flex flex-wrap gap-1.5">
          {domain.skills.map((s) => (
            <span key={s} className={`rounded-full px-2.5 py-1 text-[10px] font-medium ${c.skill}`}>
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={() => onTakeTest(domain.name)}
        className={`w-full rounded-2xl border py-2.5 text-xs font-semibold transition-all duration-200 ${c.btn}`}
      >
        View Assessment →
      </button>
    </div>
  );
};

const DomainsGrid = ({ onTakeTest }) => {
  const [headRef, headVisible] = useInView(0.1);

  return (
    <section id="domains" className="py-20">
      <div
        ref={headRef}
        className={`text-center mb-12 transition-all duration-700 ${headVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
      >
        <p className="section-label mb-3">Career paths</p>
        <h2 className="text-3xl font-bold text-white sm:text-4xl">Supported domains</h2>
        <p className="mt-3 text-slate-500 max-w-md mx-auto text-sm">
          9 career tracks, each with a tailored AI assessment and skill gap analysis.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {DOMAINS.map((d, i) => (
          <DomainCard key={d.name} domain={d} index={i} onTakeTest={onTakeTest} />
        ))}
      </div>
    </section>
  );
};

export default DomainsGrid;
