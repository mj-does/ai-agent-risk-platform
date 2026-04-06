// src/api.js
// This file connects your React app → FastAPI backend

const API_URL = "http://127.0.0.1:8000";

// 🔹 Send prompt to FastAPI risk engine
export async function analyzePrompt(prompt) {
  try {
    const res = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },

      // Must match FastAPI PromptRequest schema
      body: JSON.stringify({
        prompt: prompt,
        agent_name: "DevOps Agent",
        industry: "Technology",
        use_case: "Automation workflow"
      }),
    });

    if (!res.ok) {
      throw new Error("Backend request failed");
    }

    const data = await res.json();

    /*
      Backend returns:
      {
        status: "success",
        analysis: {
          risk_score: 0–10,
          risk_level: "Medium",
          risks_identified: []
        }
      }

      Frontend expects:
      {
        risk_score: 0–1,
        decision: "BLOCKED" | "SAFE",
        explanation: "text"
      }
    */

    const riskScoreNormalized = data.analysis.risk_score / 10;

    return {
      risk_score: riskScoreNormalized,
      decision: riskScoreNormalized > 0.4 ? "Blocked" : "Safe",
      explanation: data.analysis.risks_identified.join(", "),
    };

  } catch (err) {
    console.error(" API ERROR:", err);
    return null;
  }
}