import { useState } from "react";
import Sidebar from "./components/Sidebar";
import RiskGraph from "./components/RiskGraph";
import DetailPanel from "./components/DetailPanel";
import { analyzePrompt } from "./api";
import { attackPrompts } from "./data";

export default function App() {
  const [events, setEvents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [userPrompt, setUserPrompt] = useState("");

  const [stats, setStats] = useState({
    total: 0,
    blocked: 0,
    risk: 0,
    alerts: 0,
  });

  // 🔥 CORE FUNCTION → calls backend AI
  const analyzeAttack = async (prompt) => {
    if (!prompt) return;

    setLoading(true);
    const result = await analyzePrompt(prompt);
    setLoading(false);

    if (!result) {
      alert("Backend not connected");
      return;
    }

    const newEvent = {
      id: Date.now(),
      time: new Date().toLocaleTimeString(),
      prompt: prompt,
      risk: result.risk_score,
      status: result.decision,
      explanation: result.explanation,
    };

    setEvents((prev) => [newEvent, ...prev]);
    setSelected(newEvent);

    // 📊 update stats correctly
    setStats((prev) => ({
      total: prev.total + 1,
      blocked: result.decision === "Blocked" ? prev.blocked + 1 : prev.blocked,
      alerts: result.risk_score > 0.7 ? prev.alerts + 1 : prev.alerts,
      risk: Math.round(result.risk_score * 100),
    }));
  };

  // 🤖 Custom prompt from input
  const analyzeCustomPrompt = async () => {
    await analyzeAttack(userPrompt);
    setUserPrompt("");
  };

  // 🎲 Simulate ONE random attack
  const simulateAttack = () => {
    const randomPrompt =
      attackPrompts[Math.floor(Math.random() * attackPrompts.length)];
    analyzeAttack(randomPrompt);
  };

  // 🎬 Run demo = sequential calls (no duplicates)
  const runDemo = async () => {
    setLoading(true);
    for (let i = 0; i < attackPrompts.length; i++) {
      await analyzeAttack(attackPrompts[i]);
      await new Promise((r) => setTimeout(r, 700));
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <Sidebar events={events} onSelect={setSelected} />

      <main className="main">
        <header className="topbar">
          <h2>AI Risk Platform</h2>

          {/* ✨ CUSTOM PROMPT INPUT */}
          <div style={{ display: "flex", gap: "10px" }}>
            <input
              placeholder="Type a custom AI agent prompt..."
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              style={{
                padding: "10px",
                width: "360px",
                borderRadius: "6px",
                border: "none",
              }}
            />
            <button onClick={analyzeCustomPrompt} disabled={loading}>
              Analyze Prompt
            </button>
          </div>

          <div className="buttons">
            <button
              className="attack"
              onClick={simulateAttack}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "● Simulate attack"}
            </button>

            <button
              className="demo"
              onClick={runDemo}
              disabled={loading}
            >
              ▶ Run demo
            </button>
          </div>
        </header>

        {/* 📊 Stats */}
        <div className="stats">
          <div className="card">
            <p>Total prompts</p>
            <h3>{stats.total}</h3>
          </div>

          <div className="card">
            <p>Attacks blocked</p>
            <h3>{stats.blocked}</h3>
          </div>

          <div className="card">
            <p>Latest risk score</p>
            <h3>{stats.risk}%</h3>
          </div>

          <div className="card">
            <p>Critical alerts</p>
            <h3>{stats.alerts}</h3>
          </div>
        </div>

        <RiskGraph risk={stats.risk} />
      </main>

      <DetailPanel event={selected} />
    </div>
  );
}