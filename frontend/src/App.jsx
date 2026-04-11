import { useEffect, useMemo, useRef, useState } from "react";
import Sidebar from "./components/Sidebar";
import Badge from "./components/Badge";
import DecisionBanner from "./components/DecisionBanner";
import EvaluationDetail from "./components/EvaluationDetail";
import SettingsModal from "./components/SettingsModal";
import HeroSlideshow from "./components/HeroSlideshow";
import SiteFooter from "./components/SiteFooter";
import {
  analyzePrompt,
  getSessionId,
  verifyAdminCredentials,
  submitEscalationRequest,
} from "./api";
import RiskBlockModal from "./components/RiskBlockModal";
import AdminQueue from "./components/AdminQueue";
import { formatReasonList } from "./utils/evaluationFormat";
import { attackPrompts } from "./data";

const STORAGE_KEY = "airisk.ui.v4";

const API_CONTEXT_DEFAULTS = {
  agent_name: "DevOps Agent",
  industry: "Technology",
  use_case: "Automation workflow",
};

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

function policyDecision({ riskScore, promptText, securityStatus }, policy) {
  const text = (promptText || "").toLowerCase();
  const keywordHit = policy.requireReviewKeywords.some((k) => text.includes(k));
  if (securityStatus === "review_required") return "REVIEW";
  if (riskScore >= policy.thresholdBlock) return "BLOCK";
  if (keywordHit || riskScore >= policy.thresholdReview) return "REVIEW";
  return "ALLOW";
}

export default function App() {
  const [view, setView] = useState("dashboard");
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [evaluateOpen, setEvaluateOpen] = useState(false);

  const [promptDraft, setPromptDraft] = useState("");
  const [policy, setPolicy] = useState(defaultPolicy());
  const [evaluations, setEvaluations] = useState([]);
  const [manualOverride, setManualOverride] = useState(null);
  const lastSimIndex = useRef(-1);
  const analysisBusy = useRef(false);
  const [blockGate, setBlockGate] = useState(null);
  const [blockBusy, setBlockBusy] = useState(false);
  const [escalateBusy, setEscalateBusy] = useState(false);

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

  const selectedReasons = useMemo(() => {
    if (!selected) return [];
    return formatReasonList(selected.reasons, selected.backendExplanation);
  }, [selected]);

  async function runEvaluation(promptText, options = {}) {
    const { skipBlockUi = false, manualOverride: explicitOverride } = options;
    const trimmed = (promptText || "").trim();
    if (!trimmed) return;
    if (analysisBusy.current) return;

    const overrideForRequest =
      explicitOverride !== undefined ? explicitOverride : manualOverride;

    analysisBusy.current = true;
    setLoading(true);
    let res;
    try {
      res = await analyzePrompt(trimmed, {
        ...API_CONTEXT_DEFAULTS,
        session_id: getSessionId(),
        manual_override: overrideForRequest,
      });
    } finally {
      setLoading(false);
      analysisBusy.current = false;
    }

    if (!res) {
      setSettingsOpen(true);
      return;
    }

    setManualOverride(null);
    setEvaluateOpen(false);

    const riskScore = clamp01(res.risk_score);
    const securityStatus = res.security_status || null;
    const decision = policyDecision(
      { riskScore, promptText: trimmed, securityStatus },
      policy
    );

    const raw = res.raw && typeof res.raw === "object" ? res.raw : {};
    const pickAudit = (k) =>
      res[k] ?? raw[k] ?? raw.audit?.[k] ?? raw.analysis?.[k];
    const tgNum = (() => {
      const v = pickAudit("tg_propagated_risk");
      if (typeof v === "number" && Number.isFinite(v)) return v;
      if (typeof v === "string" && v.trim() !== "") {
        const n = Number(v);
        return Number.isFinite(n) ? n : null;
      }
      return null;
    })();
    const sysRaw = pickAudit("tg_affected_systems");
    const tgAff =
      Array.isArray(sysRaw) ? sysRaw : Array.isArray(res.tg_affected_systems) ? res.tg_affected_systems : [];

    const ev = {
      id: crypto?.randomUUID?.() || String(Date.now()),
      createdAt: new Date().toISOString(),
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
      securityStatus,
      attackCategories: Array.isArray(res.attack_categories)
        ? res.attack_categories
        : [],
      llmGuardUsed: Boolean(res.llm_guard_used),
      manualOverride: res.manual_override || null,
      adminBypass:
        explicitOverride === "force_allow" && decision === "ALLOW",
      enforcementEngine: pickAudit("enforcement_engine") ?? null,
      tgPropagatedRisk: tgNum,
      tgAffectedSystems: tgAff,
      tgDecisionReason: pickAudit("tg_decision_reason") ?? null,
    };

    setEvaluations((prev) => [ev, ...prev]);
    setSelectedId(ev.id);
    setView("dashboard");

    if (decision === "BLOCK" && !skipBlockUi) {
      setBlockGate({ prompt: trimmed, evaluation: ev });
    }
  }

  function handleBlockCancel() {
    setBlockGate(null);
  }

  async function handleBlockApprove(adminId, adminPassword) {
    if (!blockGate) return false;
    setBlockBusy(true);
    try {
      const ok = await verifyAdminCredentials(adminId, adminPassword);
      if (!ok) return false;
      const { prompt } = blockGate;
      await runEvaluation(prompt, {
        skipBlockUi: true,
        manualOverride: "force_allow",
      });
      setBlockGate(null);
      return true;
    } finally {
      setBlockBusy(false);
    }
  }

  async function handleSendToAdmin() {
    if (!blockGate?.evaluation) return;
    setEscalateBusy(true);
    try {
      const e = blockGate.evaluation;
      await submitEscalationRequest({
        prompt: e.prompt,
        prompt_id: e.promptId,
        session_id: getSessionId(),
        risk_score_normalized: e.riskScore,
        risk_level: e.riskLevel,
        decision: e.decision,
      });
      setBlockGate(null);
    } finally {
      setEscalateBusy(false);
    }
  }

  async function simulateOne() {
    if (analysisBusy.current) return;
    if (attackPrompts.length === 0) return;
    let idx = Math.floor(Math.random() * attackPrompts.length);
    if (attackPrompts.length > 1) {
      let guard = 0;
      while (idx === lastSimIndex.current && guard < 12) {
        idx = Math.floor(Math.random() * attackPrompts.length);
        guard += 1;
      }
    }
    lastSimIndex.current = idx;
    await runEvaluation(attackPrompts[idx]);
  }

  function toggleSidebar() {
    setSidebarOpen((o) => !o);
  }

  return (
    <>
      <div className="bgMotion" aria-hidden>
        <div className="bgMotionOrb bgMotionOrb1" />
        <div className="bgMotionOrb bgMotionOrb2" />
        <div className="bgMotionOrb bgMotionOrb3" />
        <div className="bgMotionOrb bgMotionOrb4" />
      </div>

      <div className={blockGate ? "appRoot appRoot--riskBanner" : "appRoot"}>
        {sidebarOpen && (
          <button
            type="button"
            className="sidebarBackdrop"
            aria-label="Close navigation"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <Sidebar
          className={`sidebarSlide ${sidebarOpen ? "sidebarSlide--open" : ""}`}
          view={view}
          onView={setView}
          evaluations={evaluations}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onOpenSettings={() => setSettingsOpen(true)}
          onClose={() => setSidebarOpen(false)}
        />

        <main className="main mainFluid">
          <header className="shellTopBar">
            <button
              type="button"
              className="hamburgerBtn"
              onClick={toggleSidebar}
              aria-expanded={sidebarOpen}
              aria-label={sidebarOpen ? "Close menu" : "Open menu"}
            >
              <span className="hamburgerBar" />
              <span className="hamburgerBar" />
              <span className="hamburgerBar" />
            </button>
            <div className="shellTopBarRight">
              <button
                type="button"
                className="btn btnGhost btnSm"
                onClick={() => setSettingsOpen(true)}
              >
                Settings
              </button>
            </div>
          </header>

          {view === "dashboard" && (
            <>
              <section className="hero heroBackdrop">
                <HeroSlideshow>
                  <h1 className="heroTitle heroTitle--onBackdrop">
                    Take control of every agent access request
                  </h1>
                  <div className="heroCtaRow heroCtaRow--onBackdrop">
                    <button
                      type="button"
                      className="btn btnHeroPrimary"
                      onClick={() => void simulateOne()}
                      disabled={loading}
                    >
                      {loading ? "Analyzing…" : "Simulate attack"}
                    </button>
                    <button
                      type="button"
                      className="btn btnHeroSecondary"
                      onClick={() => setEvaluateOpen(true)}
                      disabled={loading}
                    >
                      Evaluate prompt <span className="heroCtaArrow" aria-hidden>→</span>
                    </button>
                  </div>
                </HeroSlideshow>
              </section>

              <section className="panel posturePanel">
                <DecisionBanner
                  empty={!selected}
                  decision={selected?.decision ?? "ALLOW"}
                  riskScore={selected?.riskScore ?? 0}
                  riskLevel={selected?.riskLevel ?? null}
                  securityStatus={selected?.securityStatus}
                  llmGuardUsed={selected?.llmGuardUsed}
                  overviewStats={stats}
                />
                {selected && (
                  <div className="postureReasoning">
                    <div className="detailK detailKReasoning">Reasoning</div>
                    {selectedReasons.length === 0 ? (
                      <div className="detailMuted detailMutedLarge">
                        No reasons returned by the backend.
                      </div>
                    ) : (
                      <ul className="reasonList reasonListLarge">
                        {selectedReasons.slice(0, 12).map((r, i) => (
                          <li key={`${i}-${r}`}>{r}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </section>

              <div className="dashboardLower">
                <section className="panel panelCompact">
                  <div className="panelHeader">
                    <div>
                      <div className="panelTitle">Overview</div>
                      <p className="panelSubtitle panelSubtitleTight">
                        Roll-up of every evaluation in this browser session. Each prompt is scored,
                        checked against policy, and assigned ALLOW, REVIEW, or BLOCK before any agent
                        action. Use these numbers to see volume, how often the gate stops or escalates
                        traffic, and the mean risk across all runs.
                      </p>
                    </div>
                  </div>
                  <div className="metricGrid metricGridTight">
                    <div className="metric">
                      <div className="metricLabel">Total evaluations</div>
                      <div className="metricValue">{stats.total}</div>
                      <div className="metricHint">Prompts scored in this session</div>
                    </div>
                    <div className="metric">
                      <div className="metricLabel">Blocked</div>
                      <div className="metricValue">{stats.blocked}</div>
                      <div className="metricHint">Risk ≥ block threshold</div>
                    </div>
                    <div className="metric">
                      <div className="metricLabel">Review queue</div>
                      <div className="metricValue">{stats.review}</div>
                      <div className="metricHint">Keywords, medium risk, or review_required</div>
                    </div>
                    <div className="metric">
                      <div className="metricLabel">Avg risk</div>
                      <div className="metricValue">
                        {(stats.avgRisk * 100).toFixed(1)}%
                      </div>
                      <div className="metricHint">Mean of all risk scores (0–100%)</div>
                    </div>
                  </div>
                </section>

                <section className="panel panelGrow">
                  <div className="panelHeader">
                    <div>
                      <div className="panelTitle">Execution trace</div>
                      <div className="panelSubtitle">
                        Latest run. Open the menu to browse attack logs.
                      </div>
                    </div>
                  </div>

                  {!selected ? (
                    <div className="empty">
                      <div className="emptyTitle">No evaluations yet</div>
                      <div className="emptySub">
                        Use the buttons above to simulate or evaluate a prompt.
                      </div>
                    </div>
                  ) : (
                    <div className="detailSplit detailSplitFull detailPad">
                      <EvaluationDetail evaluation={selected} />
                    </div>
                  )}
                </section>
              </div>
            </>
          )}

          {view === "evaluations" && (
            <>
              <section className="hero heroCompact">
                <h1 className="heroTitle heroTitleSm">Attack logs</h1>
                <p className="heroLead heroLeadSm">
                  All evaluations, newest first. Select a row to open it on Control Plane.
                </p>
              </section>
              <section className="panel">
                <div className="panelHeader">
                  <div className="panelTitle">History</div>
                </div>
                {evaluations.length === 0 ? (
                  <div className="empty">
                    <div className="emptyTitle">No logs yet</div>
                    <div className="emptySub">Run a simulation or evaluation first.</div>
                  </div>
                ) : (
                  <div className="table">
                    <div className="tableHead tableHeadSophos">
                      <div>Time</div>
                      <div>Risk</div>
                      <div>Decision</div>
                      <div>Prompt</div>
                    </div>
                    {evaluations.map((e) => (
                      <button
                        key={e.id}
                        type="button"
                        className="tableRow tableRowSophos"
                        onClick={() => {
                          setSelectedId(e.id);
                          setView("dashboard");
                        }}
                      >
                        <div className="mono">
                          {new Date(e.createdAt).toLocaleString()}
                        </div>
                        <div className="mono">{(e.riskScore * 100).toFixed(1)}%</div>
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
            </>
          )}

          {view === "admin" && (
            <>
              <section className="hero heroCompact">
                <h1 className="heroTitle heroTitleSm">Admin console</h1>
                <p className="heroLead heroLeadSm">
                  Review escalation requests sent when a high-risk prompt is blocked.
                </p>
              </section>
              <AdminQueue />
            </>
          )}

          {view === "policies" && (
            <>
              <section className="hero heroCompact">
                <h1 className="heroTitle heroTitleSm">Policy</h1>
                <p className="heroLead heroLeadSm">
                  Thresholds and review keywords for routing decisions.
                </p>
              </section>
              <section className="panel">
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
                      If risk ≥ block → BLOCK. Else if keyword hit or risk ≥ review →
                      REVIEW. Else → ALLOW.
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
            </>
          )}
        </main>

        {evaluateOpen && (
          <button
            type="button"
            className="evaluateBackdrop"
            aria-label="Close evaluate panel"
            onClick={() => setEvaluateOpen(false)}
          />
        )}
        <aside
          className={`evaluateDrawer ${evaluateOpen ? "evaluateDrawer--open" : ""}`}
          aria-hidden={!evaluateOpen}
        >
          <div className="evaluateDrawerHeader">
            <div>
              <h2 className="evaluateDrawerTitle">Evaluate prompt</h2>
              <p className="evaluateDrawerSub">
                Policy: block ≥ {Math.round(policy.thresholdBlock * 100)}%, review ≥{" "}
                {Math.round(policy.thresholdReview * 100)}%
              </p>
            </div>
            <button
              type="button"
              className="iconBtn evaluateDrawerClose"
              onClick={() => setEvaluateOpen(false)}
              aria-label="Close"
            >
              ×
            </button>
          </div>
          <div className="evaluateDrawerBody">
            <label className="field">
              <span>Prompt</span>
              <textarea
                value={promptDraft}
                onChange={(e) => setPromptDraft(e.target.value)}
                placeholder="Paste or type the prompt to evaluate…"
                rows={10}
              />
            </label>
            <div className="operatorBar">
              <div className="operatorBarTitle">Operator override (next request only)</div>
              <div className="operatorBarOpts">
                {[
                  { id: null, label: "Default pipeline" },
                  { id: "force_allow", label: "Manual permit" },
                  { id: "force_block", label: "Manual block" },
                  { id: "force_review", label: "Force review" },
                ].map((o) => (
                  <label key={o.label} className="operatorOpt">
                    <input
                      type="radio"
                      name="manualOvDrawer"
                      checked={manualOverride === o.id}
                      onChange={() => setManualOverride(o.id)}
                    />
                    <span>{o.label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="evaluateDrawerActions">
              <button
                type="button"
                className="btn btnPrimary btnBlock"
                onClick={() => runEvaluation(promptDraft)}
                disabled={loading || !promptDraft.trim()}
              >
                {loading ? "Analyzing…" : "Evaluate risk"}
              </button>
              <button
                type="button"
                className="btn btnGhost btnBlock"
                onClick={() => setPromptDraft("")}
                disabled={loading || !promptDraft}
              >
                Clear
              </button>
            </div>
          </div>
        </aside>

        <SiteFooter />
      </div>

      {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}

      {blockGate && (
        <RiskBlockModal
          promptPreview={blockGate.evaluation?.prompt}
          onCancel={handleBlockCancel}
          onApprove={handleBlockApprove}
          onSendToAdmin={handleSendToAdmin}
          busyApprove={blockBusy}
          busyEscalate={escalateBusy}
        />
      )}
    </>
  );
}
