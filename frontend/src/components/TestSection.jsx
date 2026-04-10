import React, { useState, useEffect } from 'react';

const TestSection = ({ domain, onComplete, onBack }) => {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]);

  useEffect(() => {
    const fetchQuestions = async () => {
      const res = await fetch(`http://127.0.0.1:8000/get-questions/${encodeURIComponent(domain)}`);
      const data = await res.json();
      setQuestions(data.questions || []);
      setAnswers(new Array((data.questions || []).length).fill(''));
    };
    if (domain) fetchQuestions();
  }, [domain]);

  const handleAnswerChange = (index, value) => {
    const newAnswers = [...answers];
    newAnswers[index] = value;
    setAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    const res = await fetch('http://127.0.0.1:8000/evaluate-test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain, answers }),
    });
    const data = await res.json();
    console.log('API response:', data);
    onComplete(data);
  };

  const allAnswered = questions.length > 0 && answers.every(Boolean);

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] bg-slate-900/95 p-8 ring-1 ring-white/10 shadow-2xl shadow-slate-950/30">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-indigo-300">Assessment</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Test your readiness for {domain}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-400">Answer all questions to reveal your score, feedback, and areas to improve.</p>
          </div>
          <button onClick={onBack} className="rounded-full border border-slate-700 bg-slate-900/90 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white">
            Back to recommendations
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          {questions.map((q, index) => (
            <div key={index} className="rounded-[1.75rem] border border-white/10 bg-slate-900/90 p-6 shadow-lg shadow-slate-950/20">
              <p className="text-sm uppercase tracking-[0.24em] text-indigo-300">Question {index + 1}</p>
              <h3 className="mt-3 text-lg font-semibold text-white">{q.question}</h3>
              <div className="mt-5 grid gap-3">
                {q.options.map((opt, i) => (
                  <button
                    key={i}
                    onClick={() => handleAnswerChange(index, opt)}
                    className={`w-full rounded-2xl border px-4 py-3 text-left text-sm transition ${answers[index] === opt ? 'border-indigo-500 bg-indigo-500/15 text-white' : 'border-slate-700 bg-slate-950/90 text-slate-300 hover:border-indigo-500 hover:bg-slate-900/90'}`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-6">
          <div className="rounded-[2rem] border border-white/10 bg-slate-900/95 p-6 shadow-2xl shadow-slate-950/30">
            <p className="text-sm uppercase tracking-[0.24em] text-indigo-300">Progress</p>
            <div className="mt-4 flex items-center justify-between gap-4">
              <p className="text-5xl font-semibold text-white">{questions.filter((_, index) => Boolean(answers[index])).length}/{questions.length}</p>
              <span className="rounded-full bg-indigo-500/15 px-4 py-2 text-sm font-semibold text-indigo-200">{allAnswered ? 'Ready to submit' : 'Awaiting answers'}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-400">Complete all answers to unlock your readiness score and tailored feedback.</p>
          </div>

          <button
            onClick={handleSubmit}
            disabled={!allAnswered}
            className="w-full rounded-full bg-indigo-500 px-6 py-4 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700"
          >
            Submit Test
          </button>
        </div>
      </div>
    </div>
  );
};

export default TestSection;
