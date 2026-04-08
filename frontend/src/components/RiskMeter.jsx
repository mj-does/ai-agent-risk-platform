function toneForRisk(v) {
  if (v >= 0.75) return "danger";
  if (v >= 0.5) return "warning";
  if (v >= 0.25) return "info";
  return "success";
}

export default function RiskMeter({ value = 0 }) {
  const clamped = Math.max(0, Math.min(1, value));
  const pct = Math.round(clamped * 100);
  const tone = toneForRisk(clamped);

  return (
    <div className="riskMeter" aria-label={`Risk score ${pct}%`}>
      <div className="riskMeterTop">
        <div className="riskMeterLabel">Risk score</div>
        <div className={`riskMeterValue riskMeterValue-${tone}`}>{pct}%</div>
      </div>
      <div className="riskBar">
        <div className={`riskBarFill riskBarFill-${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

