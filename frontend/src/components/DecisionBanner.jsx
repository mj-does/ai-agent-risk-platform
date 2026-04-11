function riskBandFromScore(clamped) {
  if (clamped >= 0.7) return { label: "High risk", key: "high" };
  if (clamped >= 0.4) return { label: "Medium risk", key: "medium" };
  return { label: "Low risk", key: "low" };
}

function ArcGauge({ value01 }) {
  const r = 78;
  const cx = 100;
  const cy = 100;
  const arcLen = Math.PI * r;
  const d = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`;
  const progress = Math.max(0, Math.min(1, value01));
  const dashOffset = arcLen * (1 - progress);

  return (
    <svg className="riskArcSvg" viewBox="0 0 200 118" aria-hidden>
      <path
        className="riskArcTrack"
        d={d}
        fill="none"
        strokeWidth="14"
        strokeLinecap="round"
      />
      <path
        className="riskArcFill"
        d={d}
        fill="none"
        strokeWidth="14"
        strokeLinecap="round"
        strokeDasharray={`${arcLen} ${arcLen}`}
        strokeDashoffset={dashOffset}
      />
    </svg>
  );
}

export default function DecisionBanner({
  decision = "ALLOW",
  riskScore = 0,
  riskLevel = null,
  securityStatus,
  llmGuardUsed,
  overviewStats = null,
  empty = false,
}) {
  const clamped = empty ? 0 : Math.max(0, Math.min(1, riskScore));
  const pctDisplay = (clamped * 100).toFixed(1);
  const band = riskBandFromScore(clamped);
  const levelHint = empty
    ? "Awaiting evaluation"
    : riskLevel === "HIGH"
      ? "High risk"
      : riskLevel === "MEDIUM"
        ? "Medium risk"
        : riskLevel === "LOW"
          ? "Low risk"
          : band.label;

  const bandKey = empty ? "none" : band.key;

  const s = overviewStats || { total: 0, blocked: 0, review: 0, avgRisk: 0 };

  const chipLabel = empty ? "READY" : decision;
  const chipTone = empty
    ? "ready"
    : decision === "BLOCK"
      ? "block"
      : decision === "REVIEW"
        ? "review"
        : "allow";

  return (
    <div className="postureCard">
      <div className="postureCardHeader">
        <div>
          <h2 className="postureCardTitle">Agent risk posture</h2>
          <p className="postureCardSubtitle">Overall risk score</p>
        </div>
        <div className={`postureDecisionChip postureDecisionChip--${chipTone}`}>
          {chipLabel}
        </div>
      </div>

      <div className="postureCardBody">
        <div className="postureGaugeCol">
          <div className="postureGaugeWrap">
            <ArcGauge value01={clamped} />
            <div className="postureGaugeCenter">
              <div className="posturePct">{empty ? "—" : `${pctDisplay}%`}</div>
              <div className={`postureBand postureBand--${bandKey}`}>{levelHint}</div>
            </div>
          </div>
          {!empty && (
            <div className="postureFlags">
              {securityStatus === "review_required" && (
                <span className="postureFlag">Review required</span>
              )}
              {securityStatus === "elevated" && (
                <span className="postureFlag postureFlagMuted">Elevated signals</span>
              )}
              {llmGuardUsed && (
                <span className="postureFlag postureFlagMuted">LLM layer used</span>
              )}
            </div>
          )}
        </div>

        <div className="postureStatsCol">
          <div className="postureStatsGrid">
            <div className="postureStat">
              <div className="postureStatLabel">Evaluations</div>
              <div className="postureStatValue">{s.total}</div>
            </div>
            <div className="postureStat">
              <div className="postureStatLabel">Blocked</div>
              <div className="postureStatValue">{s.blocked}</div>
            </div>
            <div className="postureStat">
              <div className="postureStatLabel">Review</div>
              <div className="postureStatValue">{s.review}</div>
            </div>
            <div className="postureStat">
              <div className="postureStatLabel">Avg risk</div>
              <div className="postureStatValue">{(s.avgRisk * 100).toFixed(1)}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
