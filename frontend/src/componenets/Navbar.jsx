// components/Navbar.jsx
import React from 'react';
import { SparklesIcon } from '@heroicons/react/24/outline';

const Navbar = () => {
  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
              <SparklesIcon className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              CareerIntel
            </span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm">
            <a href="#" className="text-gray-500 hover:text-indigo-600 transition-colors">Dashboard</a>
            <a href="#" className="text-gray-500 hover:text-indigo-600 transition-colors">Assessments</a>
            <a href="#" className="text-gray-500 hover:text-indigo-600 transition-colors">Resources</a>
          </div>
          <button className="px-4 py-1.5 rounded-full bg-indigo-50 text-indigo-600 text-sm font-medium hover:bg-indigo-100 transition-colors">
            Sign In
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;