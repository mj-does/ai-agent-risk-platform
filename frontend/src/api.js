const API_STORAGE_KEY = "airisk.api.baseUrl";

function normalizeBaseUrl(url) {
  const trimmed = (url || "").trim().replace(/\/+$/, "");
  return trimmed;
}

export function getApiBaseUrl() {
  const fromEnv = normalizeBaseUrl(import.meta?.env?.VITE_API_URL);
  if (fromEnv) return fromEnv;
  try {
    const fromStorage = normalizeBaseUrl(localStorage.getItem(API_STORAGE_KEY));
    if (fromStorage) return fromStorage;
  } catch {
    // ignore
  }
  return "http://127.0.0.1:8000";
}

export function setApiBaseUrl(url) {
  try {
    localStorage.setItem(API_STORAGE_KEY, normalizeBaseUrl(url));
  } catch {
    // ignore
  }
}

const SESSION_STORAGE_KEY = "airisk.session.v1";

export function getSessionId() {
  try {
    let id = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!id) {
      id = crypto?.randomUUID?.() || `sess-${Date.now()}`;
      localStorage.setItem(SESSION_STORAGE_KEY, id);
    }
    return id;
  } catch {
    return null;
  }
}

function coerceArray(v) {
  if (!v) return [];
  if (Array.isArray(v)) return v;
  if (typeof v === "string") return v.split(",").map((s) => s.trim()).filter(Boolean);
  return [];
}

function normalizeRiskTo01(raw) {
  const n = typeof raw === "number" ? raw : Number(raw);
  if (!Number.isFinite(n)) return 0;
  if (n <= 1) return Math.max(0, Math.min(1, n));
  // heuristics:
  // - some APIs return 0–10
  // - some pipelines return 0–100 “points”
  if (n <= 10) return Math.max(0, Math.min(1, n / 10));
  return Math.max(0, Math.min(1, n / 100));
}

// Send prompt to FastAPI risk engine
export async function analyzePrompt(prompt, context = {}) {
  const API_URL = getApiBaseUrl();
  try {
    const res = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        agent_name: context.agent_name || "DevOps Agent",
        industry: context.industry || "Technology",
        use_case: context.use_case || "Automation workflow",
        session_id: context.session_id || null,
        manual_override: context.manual_override || null,
      }),
    });

    if (!res.ok) throw new Error(`Backend request failed (${res.status})`);

    const data = await res.json();

    // Supported shapes:
    // - { analysis: { risk_score: 0–10, risk_score_normalized: 0–1, risk_level, risks_identified, ... } }
    // - { data: { risk: { risk_score, risk_level, risks_identified }, policy, agent_used, ... } }
    const analysis = data?.analysis || {};
    const pipeline = data?.data || {};
    const riskFromPipeline = pipeline?.risk || {};

    const riskNorm =
      typeof analysis.risk_score_normalized === "number"
        ? normalizeRiskTo01(analysis.risk_score_normalized)
        : normalizeRiskTo01(
            analysis.risk_score ?? riskFromPipeline.risk_score ?? 0
          );

    const riskLevel =
      analysis.risk_level || riskFromPipeline.risk_level || null;
    const risksIdentified = coerceArray(
      analysis.risks_identified ?? riskFromPipeline.risks_identified
    );

    const policy = analysis.policy || pipeline.policy || null;
    const agentUsed = analysis.agent_used || pipeline.agent_used || null;
    const promptId = analysis.prompt_id || data?.prompt_id || null;
    const graphLogged =
      typeof data?.graph_logged === "boolean" ? data.graph_logged : null;

    const meta = analysis;

    return {
      risk_score: riskNorm, // 0–1
      risk_level: riskLevel,
      reasons: risksIdentified,
      explanation: risksIdentified.join(", "),
      policy,
      agent_used: agentUsed,
      prompt_id: promptId,
      graph_logged: graphLogged,
      security_status: meta.status || null,
      attack_categories: Array.isArray(meta.attack_categories)
        ? meta.attack_categories
        : [],
      llm_guard_used: Boolean(meta.llm_guard_used),
      regex_matched:
        typeof meta.regex_matched === "boolean" ? meta.regex_matched : null,
      suspicious_structure:
        typeof meta.suspicious_structure === "boolean"
          ? meta.suspicious_structure
          : null,
      session: meta.session || null,
      manual_override: meta.manual_override || null,
      raw: data,
    };
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("API ERROR:", err);
    return null;
  }
}