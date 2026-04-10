// components/SkillInput.jsx
import React, { useState } from 'react';
import { SparklesIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const SkillInput = ({ onAnalyze, isLoading }) => {
  const [skillsInput, setSkillsInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!skillsInput.trim()) return;
    const skillsArray = skillsInput.split(',').map(s => s.trim().toLowerCase()).filter(s => s);
    if (skillsArray.length === 0) return;
    onAnalyze(skillsArray);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg shadow-indigo-50 border border-indigo-100 p-6 md:p-8 transition-all duration-300">
      <div className="flex items-center gap-2 mb-4">
        <SparklesIcon className="w-5 h-5 text-indigo-500" />
        <h2 className="text-lg font-semibold text-gray-700">Enter Your Skills</h2>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="skills" className="block text-sm font-medium text-gray-600 mb-2">
            Skills (comma-separated)
          </label>
          <input
            id="skills"
            type="text"
            value={skillsInput}
            onChange={(e) => setSkillsInput(e.target.value)}
            placeholder="e.g., python, sql, machine learning, react, node.js"
            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none transition-all duration-200 text-gray-700 placeholder-gray-400"
            disabled={isLoading}
          />
          <p className="mt-2 text-xs text-gray-400">Enter skills separated by commas</p>
        </div>
        <button
          type="submit"
          disabled={isLoading || !skillsInput.trim()}
          className="w-full md:w-auto px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-xl shadow-md hover:shadow-lg hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <ArrowPathIcon className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <SparklesIcon className="w-5 h-5" />
              Analyze Skills
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default SkillInput;