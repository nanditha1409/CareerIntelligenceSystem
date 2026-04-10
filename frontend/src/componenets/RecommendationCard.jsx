// components/RecommendationCard.jsx
import React, { useState, useEffect, useRef } from 'react';
import { BriefcaseIcon, CurrencyDollarIcon, ChartBarIcon, BeakerIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

const RecommendationCard = ({ recommendation, onTakeTest }) => {
  const { domain, confidence, salary, demand, reason } = recommendation;
  const [width, setWidth] = useState(0);
  const cardRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setWidth(confidence);
        }
      },
      { threshold: 0.1 }
    );
    if (cardRef.current) observer.observe(cardRef.current);
    return () => observer.disconnect();
  }, [confidence]);

  const getDemandColor = () => {
    const demandLower = demand.toLowerCase();
    if (demandLower.includes('high')) return 'bg-green-100 text-green-700';
    if (demandLower.includes('medium')) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  return (
    <div
      ref={cardRef}
      className="group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100 hover:border-indigo-100"
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-gray-800 group-hover:text-indigo-600 transition-colors">
              {domain}
            </h3>
            <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium ${getDemandColor()}`}>
              {demand} Demand
            </span>
          </div>
          <BriefcaseIcon className="w-8 h-8 text-indigo-400 opacity-80" />
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-500">Confidence</span>
              <span className="font-medium text-gray-700">{confidence}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${width}%` }}
              />
            </div>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <div className="flex items-center gap-1 text-gray-600">
              <CurrencyDollarIcon className="w-4 h-4 text-green-500" />
              <span>{salary}</span>
            </div>
            <div className="flex items-center gap-1 text-gray-600">
              <ChartBarIcon className="w-4 h-4 text-blue-500" />
              <span>Growth: {demand}</span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-1 text-sm font-medium text-gray-700 mb-2">
              <BeakerIcon className="w-4 h-4 text-purple-500" />
              <span>Why this path?</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {reason && reason.map((r, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded-lg border border-gray-100"
                >
                  {r}
                </span>
              ))}
            </div>
          </div>
        </div>

        <button
          onClick={onTakeTest}
          className="mt-6 w-full py-2.5 rounded-xl bg-indigo-50 text-indigo-600 font-medium text-sm hover:bg-indigo-100 transition-all duration-200 flex items-center justify-center gap-2 group/btn"
        >
          Take Test
          <ArrowRightIcon className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
};

export default RecommendationCard;