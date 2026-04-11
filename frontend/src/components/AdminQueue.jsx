import { useState } from "react";
import {
  listEscalationRequests,
  dismissEscalationRequest,
} from "../api";

export default function AdminQueue() {
  const [adminPassword, setAdminPassword] = useState("");
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const data = await listEscalationRequests(adminPassword);
      setRequests(Array.isArray(data?.requests) ? data.requests : []);
    } catch (e) {
      setError(e?.message || "Failed to load queue");
      setRequests([]);
    } finally {
      setLoading(false);
    }
  }

  async function dismiss(id) {
    try {
      await dismissEscalationRequest(id, adminPassword);
      await refresh();
    } catch (e) {
      setError(e?.message || "Dismiss failed");
    }
  }

  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <div className="panelTitle">Admin escalation queue</div>
          <p className="panelSubtitle panelSubtitleTight">
            Enter the same password as <span className="mono">ADMIN_PASSWORD</span> on the API
            server, then load pending requests. Use a second browser window on this page for a
            two-role demo.
          </p>
        </div>
      </div>
      <div className="adminQueueBar">
        <label className="field adminQueuePw">
          <span>Admin password (X-Admin-Password)</span>
          <input
            type="password"
            value={adminPassword}
            onChange={(e) => setAdminPassword(e.target.value)}
            placeholder="From server env ADMIN_PASSWORD"
            autoComplete="current-password"
          />
        </label>
        <button
          type="button"
          className="btn btnPrimary"
          onClick={() => void refresh()}
          disabled={loading}
        >
          {loading ? "Loading…" : "Refresh queue"}
        </button>
      </div>
      {error && <div className="riskBlockError adminQueueErr">{error}</div>}
      {requests.length === 0 && !loading && !error ? (
        <div className="empty">
          <div className="emptyTitle">No requests loaded</div>
          <div className="emptySub">
            Refresh after a user sends a prompt request from the block screen.
          </div>
        </div>
      ) : (
        <div className="table adminQueueTable">
          <div className="tableHead tableHeadSophos">
            <div>Time</div>
            <div>Risk</div>
            <div>Prompt</div>
            <div />
          </div>
          {requests.map((r) => (
            <div key={r.id} className="tableRow tableRowSophos adminQueueRow">
              <div className="mono">
                {r.created_at ? new Date(r.created_at).toLocaleString() : "—"}
              </div>
              <div className="mono">
                {typeof r.risk_score_normalized === "number"
                  ? `${(r.risk_score_normalized * 100).toFixed(1)}%`
                  : "—"}
              </div>
              <div className="truncate">{r.prompt}</div>
              <div>
                <button
                  type="button"
                  className="btn btnGhost btnSm"
                  onClick={() => void dismiss(r.id)}
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
