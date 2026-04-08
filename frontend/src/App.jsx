import { useEffect, useMemo, useState } from "react";
import Sidebar from "./components/Sidebar";
import Badge from "./components/Badge";
import RiskMeter from "./components/RiskMeter";
import EvaluationDetail from "./components/EvaluationDetail";
import SettingsModal from "./components/SettingsModal";
import { analyzePrompt } from "./api";
import { attackPrompts } from "./data";

const STORAGE_KEY = "airisk.ui.v1";

function clamp01(n) {
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function defaultPolicy() {
  return {
    thresholdBlock: 0.6,
    thresholdReview: 0.35,
    requireReviewKeywords: [
      "credential",
      "api key",
      "exfiltrate",
      "disable monitoring",
      "delete",
      "database",
      "production",
    ],
  };
}

function policyDecision({ riskScore, promptText }, policy) {
  const text = (promptText || "").toLowerCase();
  const keywordHit = policy.requireReviewKeywords.some((k) => text.includes(k));
  if (riskScore >= policy.thresholdBlock) return "BLOCK";
  if (keywordHit || riskScore >= policy.thresholdReview) return "REVIEW";
  return "ALLOW";
}

export default function App() {
  const [view, setView] = useState("dashboard"); // dashboard | evaluations | policies
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const [draft, setDraft] = useState({
    agentName: "DevOps Agent",
    industry: "Technology",
    useCase: "Automation workflow",
    prompt: "",
  });

  const [policy, setPolicy] = useState(defaultPolicy());
  const [evaluations, setEvaluations] = useState([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed?.policy) setPolicy(parsed.policy);
      if (Array.isArray(parsed?.evaluations)) setEvaluations(parsed.evaluations);
      if (parsed?.selectedId) setSelectedId(parsed.selectedId);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ policy, evaluations, selectedId })
      );
    } catch {
      // ignore
    }
  }, [policy, evaluations, selectedId]);

  const selected = useMemo(() => {
    if (!selectedId) return evaluations[0] || null;
    return evaluations.find((e) => e.id === selectedId) || evaluations[0] || null;
  }, [evaluations, selectedId]);

  const stats = useMemo(() => {
    const total = evaluations.length;
    const blocked = evaluations.filter((e) => e.decision === "BLOCK").length;
    const review = evaluations.filter((e) => e.decision === "REVIEW").length;
    const avgRisk =
      total === 0
        ? 0
        : evaluations.reduce((acc, e) => acc + (e.riskScore || 0), 0) / total;
    return { total, blocked, review, avgRisk };
  }, [evaluations]);

  async function runEvaluation(promptText) {
    const trimmed = (promptText || "").trim();
    if (!trimmed) return;

    setLoading(true);
    const res = await analyzePrompt(trimmed, {
      agent_name: draft.agentName,
      industry: draft.industry,
      use_case: draft.useCase,
    });
    setLoading(false);

    if (!res) {
      setSettingsOpen(true);
      return;
    }

    const riskScore = clamp01(res.risk_score);
    const decision = policyDecision({ riskScore, promptText: trimmed }, policy);

    const ev = {
      id: crypto?.randomUUID?.() || String(Date.now()),
      createdAt: new Date().toISOString(),
      agentName: draft.agentName,
      industry: draft.industry,
      useCase: draft.useCase,
      prompt: trimmed,
      riskScore,
      riskLevel: res.risk_level || null,
      reasons: Array.isArray(res.reasons) ? res.reasons : [],
      backendExplanation: res.explanation || "",
      policy: res.policy || null,
      agentUsed: res.agent_used || null,
      promptId: res.prompt_id || null,
      graphLogged: typeof res.graph_logged === "boolean" ? res.graph_logged : null,
      decision,
    };

    setEvaluations((prev) => [ev, ...prev]);
    setSelectedId(ev.id);
    setView("dashboard");
  }

  async function simulateOne() {
    const randomPrompt =
      attackPrompts[Math.floor(Math.random() * attackPrompts.length)];
    await runEvaluation(randomPrompt);
  }

  async function runDemo() {
    setLoading(true);
    for (let i = 0; i < attackPrompts.length; i++) {
      // eslint-disable-next-line no-await-in-loop
      await runEvaluation(attackPrompts[i]);
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, 450));
    }
    setLoading(false);
  }

  return (
    <div className="app">
      <Sidebar
        view={view}
        onView={setView}
        evaluations={evaluations}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <main className="main">
        <header className="topbar">
          <div className="topbarTitle">
            <div className="productName">AI Agent Risk Platform</div>
            <div className="productSub">
              Detect malicious intent and prevent unsafe agent actions before access
              is granted.
            </div>
          </div>

          <div className="topbarActions">
            <button
              className="btn btnGhost"
              type="button"
              onClick={() => setSettingsOpen(true)}
            >
              Settings
            </button>
            <button
              className="btn btnDanger"
              type="button"
              onClick={simulateOne}
              disabled={loading}
            >
              {loading ? "Analyzing…" : "Simulate attack"}
            </button>
            <button
              className="btn btnPrimary"
              type="button"
              onClick={runDemo}
              disabled={loading}
            >
              Run demo
            </button>
          </div>
        </header>

        {view === "dashboard" && (
          <div className="grid">
            <section className="panel panelSpan2">
              <div className="panelHeader">
                <div>
                  <div className="panelTitle">Evaluate access request</div>
                  <div className="panelSubtitle">
                    Paste an agent prompt to assess risk and decide whether access
                    should be allowed.
                  </div>
                </div>
                <div className="panelHeaderRight">
                  <Badge tone="neutral">
                    Policy: block ≥ {Math.round(policy.thresholdBlock * 100)}%, review
                    ≥ {Math.round(policy.thresholdReview * 100)}%
                  </Badge>
                </div>
              </div>

              <div className="formGrid">
                <label className="field">
                  <span>Agent name</span>
                  <input
                    value={draft.agentName}
                    onChange={(e) =>
                      setDraft((p) => ({ ...p, agentName: e.target.value }))
                    }
                    placeholder="e.g. DevOps Agent"
                  />
                </label>
                <label className="field">
                  <span>Industry</span>
                  <input
                    value={draft.industry}
                    onChange={(e) =>
                      setDraft((p) => ({ ...p, industry: e.target.value }))
                    }
                    placeholder="e.g. Financial Services"
                  />
                </label>
                <label className="field fieldSpan2">
                  <span>Use case</span>
                  <input
                    value={draft.useCase}
                    onChange={(e) =>
                      setDraft((p) => ({ ...p, useCase: e.target.value }))
                    }
                    placeholder="e.g. CI/CD automation for infra changes"
                  />
                </label>

                <label className="field fieldSpan2">
                  <span>Prompt</span>
                  <textarea
                    value={draft.prompt}
                    onChange={(e) =>
                      setDraft((p) => ({ ...p, prompt: e.target.value }))
                    }
                    placeholder="Describe the agent’s intent and requested action…"
                    rows={5}
                  />
                </label>

                <div className="formActions fieldSpan2">
                  <button
                    className="btn btnPrimary"
                    type="button"
                    onClick={() => runEvaluation(draft.prompt)}
                    disabled={loading || !draft.prompt.trim()}
                  >
                    {loading ? "Analyzing…" : "Evaluate risk"}
                  </button>
                  <button
                    className="btn btnGhost"
                    type="button"
                    onClick={() => setDraft((p) => ({ ...p, prompt: "" }))}
                    disabled={loading || !draft.prompt}
                  >
                    Clear
                  </button>
                </div>
              </div>
            </section>

            <section className="panel">
              <div className="panelHeader">
                <div className="panelTitle">Overview</div>
              </div>

              <div className="metricGrid">
                <div className="metric">
                  <div className="metricLabel">Total evaluations</div>
                  <div className="metricValue">{stats.total}</div>
                </div>
                <div className="metric">
                  <div className="metricLabel">Blocked</div>
                  <div className="metricValue">{stats.blocked}</div>
                </div>
                <div className="metric">
                  <div className="metricLabel">Needs review</div>
                  <div className="metricValue">{stats.review}</div>
                </div>
                <div className="metric">
                  <div className="metricLabel">Average risk</div>
                  <div className="metricValue">
                    {Math.round(stats.avgRisk * 100)}%
                  </div>
                </div>
              </div>

              <div className="divider" />

              <div className="miniExplain">
                The platform computes a risk score and applies policy to decide whether
                the agent should be allowed, blocked, or routed for human approval.
              </div>
            </section>

            <section className="panel panelSpan2">
              <div className="panelHeader">
                <div>
                  <div className="panelTitle">Latest decision</div>
                  <div className="panelSubtitle">
                    Select any evaluation in the sidebar to inspect details and reasoning.
                  </div>
                </div>
              </div>

              {!selected ? (
                <div className="empty">
                  <div className="emptyTitle">No evaluations yet</div>
                  <div className="emptySub">
                    Run the demo or evaluate a prompt to see the risk/decision workflow.
                  </div>
                </div>
              ) : (
                <div className="detailSplit">
                  <div className="decisionCard">
                    <div className="decisionTop">
                      <div>
                        <div className="decisionLabel">Decision</div>
                        <div className="decisionValue">
                          <Badge
                            tone={
                              selected.decision === "BLOCK"
                                ? "danger"
                                : selected.decision === "REVIEW"
                                  ? "warning"
                                  : "success"
                            }
                          >
                            {selected.decision}
                          </Badge>
                        </div>
                      </div>
                      <RiskMeter value={selected.riskScore} />
                    </div>

                    <div className="decisionMeta">
                      <div className="metaRow">
                        <span>Agent</span>
                        <span className="metaStrong">{selected.agentName}</span>
                      </div>
                      <div className="metaRow">
                        <span>Use case</span>
                        <span className="metaStrong">{selected.useCase}</span>
                      </div>
                      <div className="metaRow">
                        <span>Risk</span>
                        <span className="metaStrong">
                          {Math.round(selected.riskScore * 100)}%
                          {selected.riskLevel ? ` · ${selected.riskLevel}` : ""}
                        </span>
                      </div>
                    </div>
                  </div>

                  <EvaluationDetail evaluation={selected} />
                </div>
              )}
            </section>
          </div>
        )}

        {view === "evaluations" && (
          <section className="panel">
            <div className="panelHeader">
              <div>
                <div className="panelTitle">Evaluations</div>
                <div className="panelSubtitle">
                  Browse all past evaluations, sorted by newest first.
                </div>
              </div>
            </div>

            {evaluations.length === 0 ? (
              <div className="empty">
                <div className="emptyTitle">No evaluations to show</div>
                <div className="emptySub">
                  Go to Dashboard and run an evaluation to populate history.
                </div>
              </div>
            ) : (
              <div className="table">
                <div className="tableHead">
                  <div>Time</div>
                  <div>Agent</div>
                  <div>Risk</div>
                  <div>Decision</div>
                  <div>Prompt</div>
                </div>
                {evaluations.map((e) => (
                  <button
                    key={e.id}
                    type="button"
                    className="tableRow"
                    onClick={() => {
                      setSelectedId(e.id);
                      setView("dashboard");
                    }}
                  >
                    <div className="mono">
                      {new Date(e.createdAt).toLocaleString()}
                    </div>
                    <div>{e.agentName}</div>
                    <div className="mono">{Math.round(e.riskScore * 100)}%</div>
                    <div>
                      <Badge
                        tone={
                          e.decision === "BLOCK"
                            ? "danger"
                            : e.decision === "REVIEW"
                              ? "warning"
                              : "success"
                        }
                      >
                        {e.decision}
                      </Badge>
                    </div>
                    <div className="truncate">{e.prompt}</div>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {view === "policies" && (
          <section className="panel">
            <div className="panelHeader">
              <div>
                <div className="panelTitle">Policy</div>
                <div className="panelSubtitle">
                  Tune the decision thresholds and keyword triggers that route requests for
                  review or block them outright.
                </div>
              </div>
            </div>

            <div className="policyGrid">
              <div className="policyBlock">
                <div className="policyTitle">Decision thresholds</div>

                <label className="rangeField">
                  <span>
                    Block threshold:{" "}
                    <strong>{Math.round(policy.thresholdBlock * 100)}%</strong>
                  </span>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={policy.thresholdBlock}
                    onChange={(e) =>
                      setPolicy((p) => ({
                        ...p,
                        thresholdBlock: clamp01(Number(e.target.value)),
                      }))
                    }
                  />
                </label>

                <label className="rangeField">
                  <span>
                    Review threshold:{" "}
                    <strong>{Math.round(policy.thresholdReview * 100)}%</strong>
                  </span>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={policy.thresholdReview}
                    onChange={(e) =>
                      setPolicy((p) => ({
                        ...p,
                        thresholdReview: clamp01(Number(e.target.value)),
                      }))
                    }
                  />
                </label>

                <div className="policyHint">
                  If risk ≥ block → BLOCK. Else if keyword hit or risk ≥ review → REVIEW.
                  Else → ALLOW.
                </div>
              </div>

              <div className="policyBlock">
                <div className="policyTitle">Review keywords</div>
                <div className="policyHint">
                  One keyword match forces REVIEW even at lower risk scores.
                </div>
                <textarea
                  className="policyTextarea"
                  value={policy.requireReviewKeywords.join("\n")}
                  onChange={(e) =>
                    setPolicy((p) => ({
                      ...p,
                      requireReviewKeywords: e.target.value
                        .split("\n")
                        .map((s) => s.trim())
                        .filter(Boolean),
                    }))
                  }
                  rows={10}
                />
              </div>
            </div>
          </section>
        )}
      </main>

      {settingsOpen && (
        <SettingsModal onClose={() => setSettingsOpen(false)} />
      )}
    </div>
  );
}