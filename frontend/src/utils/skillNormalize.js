/**
 * Canonical skill tokens must stay aligned with backend `SKILLS_LIST` / ML feature order.
 * Input: lowercase, trim, apply alias map before API calls.
 */

const SKILL_MAP = {
  ml: 'ml',
  'machine learning': 'ml',
  ai: 'ml',
  'artificial intelligence': 'ml',
  c: 'c',
  'c++': 'cpp',
  cpp: 'cpp',
  ruby: 'ruby',
};

const LEGACY_ALIASES = {
  mysql: 'sql',
  postgres: 'sql',
  postgresql: 'sql',
  sqlite: 'sql',
  javascript: 'js',
  nodejs: 'node',
  reactjs: 'react',
  nextjs: 'react',
  'next.js': 'react',
  vuejs: 'js',
  angular: 'js',
  machinelearning: 'ml',
  'deep learning': 'ml',
  'aws cloud': 'aws',
  'amazon web services': 'aws',
  'linux os': 'linux',
  ubuntu: 'linux',
  debian: 'linux',
  'excel sheets': 'excel',
  'google sheets': 'excel',
  'power bi': 'powerbi',
  'powerbi desktop': 'powerbi',
  'cyber security': 'security',
  cybersecurity: 'security',
  infosec: 'security',
  k8s: 'kubernetes',
  kube: 'kubernetes',
  ts: 'typescript',
  mongo: 'mongodb',
  gql: 'graphql',
  tf: 'tensorflow',
  pt: 'pytorch',
  pyspark: 'spark',
  'tableau desktop': 'tableau',
};

function normalizeToken(raw) {
  let s = String(raw).trim().toLowerCase().replace(/-/g, ' ');
  s = s.replace(/\s+/g, ' ');
  if (!s) return '';

  if (SKILL_MAP[s] !== undefined) return SKILL_MAP[s];
  if (LEGACY_ALIASES[s] !== undefined) return LEGACY_ALIASES[s];

  return s;
}

/** Normalize a list of raw skill strings; dedupe while preserving order. */
export function normalizeSkillList(rawSkills) {
  const seen = new Set();
  const out = [];
  for (const raw of rawSkills) {
    const c = normalizeToken(raw);
    if (!c || seen.has(c)) continue;
    seen.add(c);
    out.push(c);
  }
  return out;
}

export default normalizeSkillList;
