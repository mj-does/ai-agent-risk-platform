/* Bumped so an old saved :8000 URL cannot override the dev default :8080. */
const API_STORAGE_KEY = "airisk.api.baseUrl.v2";

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
  return "http://127.0.0.1:8080";
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
    const auditTop = data?.audit || {};
    /* Prefer nested audit/analysis; fall back to top-level keys (API mirrors these). */
    const audit = {
      enforcement_engine:
        auditTop.enforcement_engine ??
        analysis?.enforcement_engine ??
        data?.enforcement_engine ??
        null,
      tg_propagated_risk:
        auditTop.tg_propagated_risk ??
        analysis?.tg_propagated_risk ??
        data?.tg_propagated_risk ??
        null,
      tg_affected_systems:
        auditTop.tg_affected_systems ??
        analysis?.tg_affected_systems ??
        data?.tg_affected_systems ??
        null,
      tg_decision_reason:
        auditTop.tg_decision_reason ??
        analysis?.tg_decision_reason ??
        data?.tg_decision_reason ??
        null,
    };

    function numOrNull(v) {
      if (typeof v === "number" && Number.isFinite(v)) return v;
      if (typeof v === "string" && v.trim() !== "") {
        const n = Number(v);
        return Number.isFinite(n) ? n : null;
      }
      return null;
    }

    const tgPropagated = numOrNull(audit.tg_propagated_risk);

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
      enforcement_engine: audit.enforcement_engine ?? null,
      tg_propagated_risk: tgPropagated,
      tg_affected_systems: Array.isArray(audit.tg_affected_systems)
        ? audit.tg_affected_systems
        : [],
      tg_decision_reason: audit.tg_decision_reason ?? null,
      raw: data,
    };
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("API ERROR:", err);
    return null;
  }
}

export async function verifyAdminCredentials(adminId, adminPassword) {
  const API_URL = getApiBaseUrl();
  try {
    const res = await fetch(`${API_URL}/admin/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        admin_id: adminId,
        admin_password: adminPassword,
      }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data?.ok);
  } catch {
    return false;
  }
}

export async function submitEscalationRequest(payload) {
  const API_URL = getApiBaseUrl();
  const res = await fetch(`${API_URL}/admin/escalation_requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Escalation failed (${res.status})`);
  return res.json();
}

export async function listEscalationRequests(adminPassword) {
  const API_URL = getApiBaseUrl();
  const res = await fetch(`${API_URL}/admin/escalation_requests`, {
    headers: {
      "X-Admin-Password": adminPassword || "",
    },
  });
  if (!res.ok) throw new Error(`List failed (${res.status})`);
  return res.json();
}

export async function dismissEscalationRequest(requestId, adminPassword) {
  const API_URL = getApiBaseUrl();
  const res = await fetch(`${API_URL}/admin/escalation_requests/${requestId}`, {
    method: "DELETE",
    headers: {
      "X-Admin-Password": adminPassword || "",
    },
  });
  if (!res.ok) throw new Error(`Dismiss failed (${res.status})`);
  return res.json();
}