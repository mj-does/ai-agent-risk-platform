const CATEGORY_LABELS = {
  injection: "Injection",
  escalation: "Escalation",
  exfiltration: "Exfiltration",
  persistence: "Persistence",
};

function categoryTone(cat) {
  if (cat === "exfiltration") return "danger";
  if (cat === "escalation") return "warning";
  if (cat === "persistence") return "warning";
  if (cat === "injection") return "info";
  return "neutral";
}

const STEP_ICONS = {
  Ingress: (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M12 3v12M8 11l4 4 4-4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 21h16" strokeLinecap="round" />
    </svg>
  ),
  Router: (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.75">
      <circle cx="6" cy="6" r="3" />
      <circle cx="18" cy="18" r="3" />
      <path d="M8.5 8.5l7 7M15.5 8.5l-7 7" strokeLinecap="round" />
    </svg>
  ),
  Policy: (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeLinejoin="round" />
    </svg>
  ),
  Risk: (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M4 19V5M10 19V10M16 19v-6M22 19V8" strokeLinecap="round" />
    </svg>
  ),
  Decision: (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M9 12l2 2 4-4M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
    </svg>
  ),
};

export default function EvaluationDetail({ evaluation }) {
  const policyStatus = evaluation?.policy?.status || null;
  const policyViolations = Array.isArray(evaluation?.policy?.violations)
    ? evaluation.policy.violations
    : [];
  const categories = Array.isArray(evaluation?.attackCategories)
    ? evaluation.attackCategories
    : [];

  const statusLine =
    evaluation?.securityStatus ||
    evaluation?.decision ||
    "—";

  const steps = [
    { k: "Ingress", v: "Prompt received & normalized", ok: true },
    { k: "Router", v: evaluation?.agentUsed || "Agent selected", ok: true },
    {
      k: "Policy",
      v: policyStatus === "fail" ? "Violations detected" : "Rules evaluated",
      ok: policyStatus !== "fail",
    },
    { k: "Risk", v: "Scoring + session / LLM layers", ok: true },
    { k: "Decision", v: evaluation?.decision || "—", ok: evaluation?.decision !== "BLOCK" },
  ];

  return (
    <div className="detailPanel">
      <div className="detailHeader">
        <div>
          <div className="detailSub">
            {evaluation?.createdAt ? new Date(evaluation.createdAt).toLocaleString() : ""}
          </div>
        </div>
        <span
          className={`execDecisionPill execDecisionPill--${
            evaluation?.decision === "BLOCK"
              ? "block"
              : evaluation?.decision === "REVIEW"
                ? "review"
                : "allow"
          }`}
        >
          {evaluation?.decision || "—"}
        </span>
      </div>

      <div className="attackChain">
        <div className="attackChainTitle">Attack chain</div>
        <div className="execTraceCards">
          {steps.map((s) => (
            <div
              key={s.k}
              className={`execTraceCard ${s.ok ? "" : "execTraceCard--bad"}`}
            >
              <div className="execTraceCardIcon" aria-hidden>
                {STEP_ICONS[s.k] || null}
              </div>
              <div className="execTraceCardK">{s.k}</div>
              <div className="execTraceCardV">{s.v}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="detailBlock detailMetaStrip">
        <div className="detailMetaCell">
          <div className="detailK">Prompt</div>
          <div className="detailMetaPrompt">{evaluation?.prompt || "—"}</div>
        </div>
        <div className="detailMetaCell">
          <div className="detailK">Policy</div>
          <div className="detailV">{policyStatus || "—"}</div>
        </div>
        <div className="detailMetaCell">
          <div className="detailK">Agent</div>
          <div className="detailV">{evaluation?.agentUsed || "—"}</div>
        </div>
        <div className="detailMetaCell">
          <div className="detailK">Status</div>
          <div className="detailV">{statusLine}</div>
        </div>
      </div>

      {categories.length > 0 && (
        <div className="detailBlock">
          <div className="detailK">Attack pattern categories</div>
          <div className="violationBadges">
            {categories.map((c) => (
              <span key={c} className={`catBadge catBadge--${categoryTone(c)}`}>
                {CATEGORY_LABELS[c] || c}
              </span>
            ))}
          </div>
        </div>
      )}

      {policyViolations.length > 0 && (
        <div className="detailBlock">
          <div className="detailK">Policy violations</div>
          <div className="violationBadges">
            {policyViolations.slice(0, 12).map((v) => (
              <span key={v} className="violationBadge">
                {v}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="auditFieldsSection">
        <div className="detailK auditFieldsSectionTitle">Audit fields</div>
        <div className="auditFieldsGrid">
          <div className="detailBlock auditFieldBlock">
            <div className="detailK">Evaluation ID</div>
            <div className="auditFieldValue mono">{evaluation?.id || "—"}</div>
          </div>
          <div className="detailBlock auditFieldBlock">
            <div className="detailK">TigerGraph prompt_id</div>
            <div className="auditFieldValue mono">{evaluation?.promptId || "—"}</div>
          </div>
          <div className="detailBlock auditFieldBlock">
            <div className="detailK">Graph logged</div>
            <div className="auditFieldValue mono">
              {typeof evaluation?.graphLogged === "boolean"
                ? String(evaluation.graphLogged)
                : "—"}
            </div>
          </div>
          <div className="detailBlock auditFieldBlock">
            <div className="detailK">Risk score (normalized)</div>
            <div className="auditFieldValue mono">
              {typeof evaluation?.riskScore === "number"
                ? evaluation.riskScore.toFixed(4)
                : "—"}
            </div>
          </div>
          {evaluation?.securityStatus && (
            <div className="detailBlock auditFieldBlock">
              <div className="detailK">Security status</div>
              <div className="auditFieldValue mono">{evaluation.securityStatus}</div>
            </div>
          )}
          {evaluation?.manualOverride && (
            <div className="detailBlock auditFieldBlock">
              <div className="detailK">Operator override</div>
              <div className="auditFieldValue mono">{evaluation.manualOverride}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
