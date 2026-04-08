import Badge from "./Badge";

function formatReasonList(reasons, backendExplanation) {
  const list = Array.isArray(reasons) ? reasons.filter(Boolean) : [];
  if (list.length) return list;
  if (backendExplanation && backendExplanation.trim()) return [backendExplanation.trim()];
  return [];
}

export default function EvaluationDetail({ evaluation }) {
  const reasons = formatReasonList(evaluation?.reasons, evaluation?.backendExplanation);
  const policyStatus = evaluation?.policy?.status || null;
  const policyViolations = Array.isArray(evaluation?.policy?.violations)
    ? evaluation.policy.violations
    : [];

  return (
    <div className="detailPanel">
      <div className="detailHeader">
        <div>
          <div className="detailTitle">Evaluation detail</div>
          <div className="detailSub">
            {evaluation?.createdAt ? new Date(evaluation.createdAt).toLocaleString() : ""}
          </div>
        </div>
        <Badge
          tone={
            evaluation?.decision === "BLOCK"
              ? "danger"
              : evaluation?.decision === "REVIEW"
                ? "warning"
                : "success"
          }
        >
          {evaluation?.decision || "—"}
        </Badge>
      </div>

      <div className="detailBlock">
        <div className="detailK">Prompt</div>
        <div className="detailPrompt">{evaluation?.prompt || "—"}</div>
      </div>

      <div className="detailGrid">
        <div className="detailBlock">
          <div className="detailK">Agent</div>
          <div className="detailV">{evaluation?.agentName || "—"}</div>
        </div>
        <div className="detailBlock">
          <div className="detailK">Industry</div>
          <div className="detailV">{evaluation?.industry || "—"}</div>
        </div>
        <div className="detailBlock detailSpan2">
          <div className="detailK">Use case</div>
          <div className="detailV">{evaluation?.useCase || "—"}</div>
        </div>
      </div>

      <div className="detailGrid">
        <div className="detailBlock">
          <div className="detailK">Policy status</div>
          <div className="detailV">{policyStatus || "—"}</div>
        </div>
        <div className="detailBlock">
          <div className="detailK">Pipeline agent</div>
          <div className="detailV">{evaluation?.agentUsed || "—"}</div>
        </div>
      </div>

      {policyViolations.length > 0 && (
        <div className="detailBlock">
          <div className="detailK">Policy violations</div>
          <ul className="reasonList">
            {policyViolations.slice(0, 8).map((v, i) => (
              <li key={`${i}-${v}`}>{v}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="detailBlock">
        <div className="detailK">Reasoning</div>
        {reasons.length === 0 ? (
          <div className="detailMuted">No reasons returned by the backend.</div>
        ) : (
          <ul className="reasonList">
            {reasons.slice(0, 8).map((r, i) => (
              <li key={`${i}-${r}`}>{r}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="detailBlock">
        <div className="detailK">Audit fields</div>
        <div className="auditRows">
          <div className="auditRow">
            <span>Evaluation ID</span>
            <span className="mono">{evaluation?.id || "—"}</span>
          </div>
          <div className="auditRow">
            <span>TigerGraph prompt_id</span>
            <span className="mono">{evaluation?.promptId || "—"}</span>
          </div>
          <div className="auditRow">
            <span>Graph logged</span>
            <span className="mono">
              {typeof evaluation?.graphLogged === "boolean"
                ? String(evaluation.graphLogged)
                : "—"}
            </span>
          </div>
          <div className="auditRow">
            <span>Risk score</span>
            <span className="mono">
              {typeof evaluation?.riskScore === "number"
                ? evaluation.riskScore.toFixed(2)
                : "—"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

