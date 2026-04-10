// components/TestSection.jsx
import React, { useState, useEffect } from 'react';
import { ArrowLeftIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const TestSection = ({ domain, onComplete, onBack }) => {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setLoading(true);
        const encodedDomain = encodeURIComponent(domain);
        const response = await fetch(`http://127.0.0.1:8000/get-questions/${encodedDomain}`);
        if (!response.ok) throw new Error('Failed to load questions');
        const data = await response.json();
        setQuestions(data.questions || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchQuestions();
  }, [domain]);

  const handleAnswer = (questionIndex, selectedOption) => {
    setAnswers(prev => ({ ...prev, [questionIndex]: selectedOption }));
  };

  const handleSubmit = async () => {
    const allAnswered = questions.every((_, idx) => answers[idx]);
    if (!allAnswered) {
      alert('Please answer all questions before submitting.');
      return;
    }

    setSubmitting(true);
    try {
      const answerList = questions.map((_, idx) => answers[idx]);
      const response = await fetch('http://127.0.0.1:8000/evaluate-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, answers: answerList }),
      });
      if (!response.ok) throw new Error('Failed to evaluate test');
      const result = await response.json();
      onComplete(result);
    } catch (err) {
      alert('Failed to submit test. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const progress = (Object.keys(answers).length / questions.length) * 100;

  if (loading) {
    return (
      <div className="mt-8 bg-white rounded-2xl shadow-sm p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="space-y-3">
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-8 bg-red-50 rounded-2xl p-8 text-center">
        <p className="text-red-600">Failed to load questions: {error}</p>
        <button onClick={onBack} className="mt-4 text-indigo-600">Go Back</button>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  const isLast = currentIndex === questions.length - 1;

  return (
    <div className="mt-8 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-100 flex items-center justify-between">
        <button onClick={onBack} className="flex items-center gap-2 text-gray-500 hover:text-indigo-600 transition-colors">
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Recommendations
        </button>
        <div className="text-sm text-gray-500">
          Question {currentIndex + 1} of {questions.length}
        </div>
      </div>

      <div className="p-6 md:p-8">
        <div className="mb-6">
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="mb-8">
          <h3 className="text-xl font-semibold text-gray-800 mb-6">{currentQuestion.question}</h3>
          <div className="space-y-3">
            {currentQuestion.options.map((option, optIdx) => (
              <label
                key={optIdx}
                className={`flex items-center p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                  answers[currentIndex] === option
                    ? 'border-indigo-300 bg-indigo-50 ring-2 ring-indigo-200'
                    : 'border-gray-200 hover:border-indigo-200 hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name={`q${currentIndex}`}
                  value={option}
                  checked={answers[currentIndex] === option}
                  onChange={() => handleAnswer(currentIndex, option)}
                  className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="ml-3 text-gray-700">{option}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={() => setCurrentIndex(prev => prev - 1)}
            disabled={currentIndex === 0}
            className="px-4 py-2 rounded-lg text-gray-500 disabled:opacity-30 disabled:cursor-not-allowed hover:text-indigo-600 transition-colors"
          >
            Previous
          </button>
          {!isLast ? (
            <button
              onClick={() => setCurrentIndex(prev => prev + 1)}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitting || Object.keys(answers).length !== questions.length}
              className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? 'Submitting...' : 'Submit Test'}
              {!submitting && <CheckCircleIcon className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestSection;