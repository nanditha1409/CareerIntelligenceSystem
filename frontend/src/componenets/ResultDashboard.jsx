// components/ResultDashboard.jsx
import React, { useState, useEffect, useRef } from 'react';
import { ChartBarIcon, LightBulbIcon, ArrowPathIcon, HomeIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const ResultDashboard = ({ result, domain, onRetake, onNewSearch }) => {
  const { score, feedback, weak_areas } = result;
  const [animatedScore, setAnimatedScore] = useState(0);
  const circleRef = useRef(null);

  useEffect(() => {
    const duration = 1000;
    const stepTime = 20;
    const steps = duration / stepTime;
    const increment = score / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setAnimatedScore(score);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.floor(current));
      }
    }, stepTime);
    return () => clearInterval(timer);
  }, [score]);

  const getScoreColor = () => {
    if (score >= 70) return 'text-green-500';
    if (score >= 40) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreGradient = () => {
    if (score >= 70) return 'from-green-400 to-emerald-500';
    if (score >= 40) return 'from-yellow-400 to-amber-500';
    return 'from-red-400 to-rose-500';
  };

  const circumference = 2 * Math.PI * 90;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="mt-8 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 border-b border-indigo-100">
          <h2 className="text-2xl font-bold text-gray-800">Assessment Results</h2>
          <p className="text-gray-600 mt-1">Domain: <span className="font-medium text-indigo-600">{domain}</span></p>
        </div>

        <div className="p-6 md:p-8">
          <div className="flex flex-col md:flex-row gap-8 items-center justify-between">
            {/* Circular Score */}
            <div className="relative w-48 h-48">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
                <circle
                  cx="100"
                  cy="100"
                  r="90"
                  fill="none"
                  stroke="#e5e7eb"
                  strokeWidth="12"
                />
                <circle
                  cx="100"
                  cy="100"
                  r="90"
                  fill="none"
                  stroke="url(#scoreGradient)"
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  className="transition-all duration-1000 ease-out"
                />
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor={score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444'} />
                    <stop offset="100%" stopColor={score >= 70 ? '#059669' : score >= 40 ? '#d97706' : '#dc2626'} />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-4xl font-bold ${getScoreColor()}`}>{animatedScore}%</span>
                <span className="text-xs text-gray-400 mt-1">Score</span>
              </div>
            </div>

            {/* Feedback & Weak Areas */}
            <div className="flex-1 space-y-6">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-indigo-50 rounded-xl">
                  <LightBulbIcon className="w-6 h-6 text-indigo-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700 mb-1">Feedback</h3>
                  <p className="text-gray-600 leading-relaxed">{feedback}</p>
                </div>
              </div>

              {weak_areas && weak_areas.length > 0 && (
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-amber-50 rounded-xl">
                    <ExclamationTriangleIcon className="w-6 h-6 text-amber-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-700 mb-2">Areas to Improve</h3>
                    <div className="flex flex-wrap gap-2">
                      {weak_areas.map((area, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1.5 bg-amber-50 text-amber-700 text-sm rounded-lg border border-amber-100"
                        >
                          {area}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 mt-8 pt-6 border-t border-gray-100">
            <button
              onClick={onRetake}
              className="flex-1 py-2.5 rounded-xl bg-indigo-50 text-indigo-600 font-medium hover:bg-indigo-100 transition-all flex items-center justify-center gap-2"
            >
              <ArrowPathIcon className="w-4 h-4" />
              Retake Test
            </button>
            <button
              onClick={onNewSearch}
              className="flex-1 py-2.5 rounded-xl bg-gray-50 text-gray-600 font-medium hover:bg-gray-100 transition-all flex items-center justify-center gap-2"
            >
              <HomeIcon className="w-4 h-4" />
              New Career Search
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultDashboard;