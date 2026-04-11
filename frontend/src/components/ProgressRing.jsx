import React, { useEffect, useState } from 'react';

/**
 * Animated SVG progress ring.
 * props: value (0–100), size?, strokeWidth?, label?, sublabel?
 */
const ProgressRing = ({ value = 0, size = 140, strokeWidth = 10, label, sublabel, color = '#6366F1' }) => {
  const [displayed, setDisplayed] = useState(0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (displayed / 100) * circumference;

  // Animate on mount / value change
  useEffect(() => {
    const timer = setTimeout(() => setDisplayed(value), 80);
    return () => clearTimeout(timer);
  }, [value]);

  const labelColor =
    value >= 75 ? '#34D399' :
    value >= 45 ? '#FBBF24' :
                  '#F87171';

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Track */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="progress-ring-circle"
            style={{ filter: `drop-shadow(0 0 8px ${color}80)` }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color: labelColor }}>{displayed}%</span>
          {sublabel && <span className="text-[10px] text-slate-500 mt-0.5">{sublabel}</span>}
        </div>
      </div>
      {label && <p className="text-xs font-medium text-slate-400 text-center">{label}</p>}
    </div>
  );
};

export default ProgressRing;
