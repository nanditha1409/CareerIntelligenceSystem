import React, { useState } from "react";

function App() {
  const [skills, setSkills] = useState("");
  const [result, setResult] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [answers, setAnswers] = useState([]);
  const [score, setScore] = useState(null);

  const handleSubmit = async () => {
    const skillArray = skills.split(",").map(s => s.trim().toLowerCase());

    const res = await fetch("http://127.0.0.1:8000/recommend-career", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ skills: skillArray })
    });

    const data = await res.json();
    setResult(data);
    setQuestions([]);
    setScore(null);
  };

  const fetchQuestions = async (domain) => {
    setSelectedDomain(domain);

    const res = await fetch(
      `http://127.0.0.1:8000/get-questions/${encodeURIComponent(domain)}`
    );

    const data = await res.json();
    setQuestions(data.questions || []);
    setAnswers(new Array(data.questions.length).fill(""));
    setScore(null);
  };

  const submitTest = async () => {
    const res = await fetch("http://127.0.0.1:8000/evaluate-test", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        domain: selectedDomain,
        answers: answers
      })
    });

    const data = await res.json();
    setScore(data.score);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#f9fbff",
      fontFamily: "Inter, sans-serif",
      padding: "40px"
    }}>

      {/* HERO */}
      <div style={{ textAlign: "center", marginBottom: "40px" }}>
        <h1 style={{
          fontSize: "48px",
          fontWeight: "800",
          color: "#111827"
        }}>
          Find Your Ideal Career
        </h1>

        <p style={{
          color: "#6b7280",
          marginTop: "10px"
        }}>
          AI-powered career guidance in seconds
        </p>
      </div>

      {/* INPUT */}
      <div style={{
        display: "flex",
        justifyContent: "center",
        gap: "10px",
        marginBottom: "40px"
      }}>
        <input
          type="text"
          placeholder="python, sql, ml..."
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
          style={{
            padding: "14px",
            width: "300px",
            borderRadius: "10px",
            border: "1px solid #e5e7eb"
          }}
        />

        <button
          onClick={handleSubmit}
          style={{
            padding: "14px 20px",
            borderRadius: "10px",
            border: "none",
            background: "#2563eb",
            color: "white",
            fontWeight: "600",
            cursor: "pointer"
          }}
        >
          Analyze
        </button>
      </div>

      {/* RESULTS */}
      {result && result.recommendations && (
        <div style={{
          maxWidth: "800px",
          margin: "auto"
        }}>
          {result.recommendations.map((rec, index) => (
            <div key={index} style={{
              background: "white",
              padding: "20px",
              borderRadius: "14px",
              marginBottom: "20px",
              border: "1px solid #e5e7eb"
            }}>
              <h3 style={{ fontSize: "20px", fontWeight: "600" }}>
                {rec.domain}
              </h3>

              <p style={{ color: "#6b7280" }}>
                {rec.confidence}% match
              </p>

              <button
                onClick={() => fetchQuestions(rec.domain)}
                style={{
                  marginTop: "10px",
                  background: "#111827",
                  color: "white",
                  padding: "8px 12px",
                  borderRadius: "8px",
                  border: "none",
                  cursor: "pointer"
                }}
              >
                Take Test →
              </button>
            </div>
          ))}
        </div>
      )}

      {/* TEST */}
      {questions.length > 0 && (
        <div style={{
          maxWidth: "700px",
          margin: "40px auto"
        }}>
          <h2>{selectedDomain} Test</h2>

          {questions.map((q, index) => (
            <div key={index} style={{ marginBottom: "20px" }}>
              <p>{q.question}</p>

              {q.options.map((opt, i) => (
                <label key={i} style={{ display: "block" }}>
                  <input
                    type="radio"
                    name={`q-${index}`}
                    value={opt}
                    onChange={() => {
                      const newAnswers = [...answers];
                      newAnswers[index] = opt;
                      setAnswers(newAnswers);
                    }}
                  />
                  {opt}
                </label>
              ))}
            </div>
          ))}

          <button
            onClick={submitTest}
            style={{
              background: "#2563eb",
              color: "white",
              padding: "10px 20px",
              borderRadius: "10px",
              border: "none"
            }}
          >
            Submit Test
          </button>
        </div>
      )}

      {/* SCORE */}
      {score !== null && (
        <div style={{ textAlign: "center", marginTop: "30px" }}>
          <h2>Your Score: {score}%</h2>
        </div>
      )}
    </div>
  );
}

export default App;