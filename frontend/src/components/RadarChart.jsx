import React from 'react';

/**
 * Pure SVG radar chart — no external deps.
 * props:
 *   labels: string[]
 *   userValues: number[]   (0–1)
 *   domainValues: number[] (0–1)
 *   size?: number
 */
const RadarChart = ({ labels = [], userValues = [], domainValues = [], size = 260 }) => {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.36;
  const levels = 4;
  const n = labels.length;
  if (n < 3) return null;

  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2;
  const point = (val, i) => ({
    x: cx + r * val * Math.cos(angle(i)),
    y: cy + r * val * Math.sin(angle(i)),
  });
  const toPath = (values) =>
    values.map((v, i) => point(v, i)).map(({ x, y }, i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ') + ' Z';

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} className="overflow-visible">
      {/* Grid rings */}
      {Array.from({ length: levels }).map((_, lvl) => {
        const frac = (lvl + 1) / levels;
        const pts = Array.from({ length: n }, (_, i) => point(frac, i));
        const d = pts.map(({ x, y }, i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ') + ' Z';
        return <path key={lvl} d={d} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />;
      })}

      {/* Axis lines */}
      {Array.from({ length: n }).map((_, i) => {
        const { x, y } = point(1, i);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />;
      })}

      {/* Domain area (target) */}
      <path
        d={toPath(domainValues)}
        fill="rgba(79,70,229,0.12)"
        stroke="rgba(79,70,229,0.4)"
        strokeWidth="1.5"
        strokeDasharray="4 3"
        className="radar-polygon"
      />

      {/* User area */}
      <path
        d={toPath(userValues)}
        fill="rgba(139,92,246,0.25)"
        stroke="rgba(139,92,246,0.9)"
        strokeWidth="2"
        className="radar-polygon"
      />

      {/* User dots */}
      {userValues.map((v, i) => {
        const { x, y } = point(v, i);
        return (
          <circle key={i} cx={x} cy={y} r="4" fill="#8B5CF6" stroke="rgba(139,92,246,0.4)" strokeWidth="6" />
        );
      })}

      {/* Labels */}
      {labels.map((label, i) => {
        const { x, y } = point(1.22, i);
        const anchor = x < cx - 4 ? 'end' : x > cx + 4 ? 'start' : 'middle';
        return (
          <text
            key={i}
            x={x}
            y={y}
            textAnchor={anchor}
            dominantBaseline="middle"
            fontSize="10"
            fontFamily="Inter, sans-serif"
            fontWeight="500"
            fill="rgba(148,163,184,0.9)"
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
};

export default RadarChart;
