import { useState } from "react";

export default function RiskBlockModal({
  promptPreview,
  onCancel,
  onApprove,
  onSendToAdmin,
  busyApprove,
  busyEscalate,
}) {
  const [adminId, setAdminId] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [approveError, setApproveError] = useState(null);
  const [escalateMsg, setEscalateMsg] = useState(null);

  async function handleApprove(e) {
    e.preventDefault();
    setApproveError(null);
    const ok = await onApprove(adminId.trim(), adminPassword);
    if (!ok) {
      setApproveError("Invalid admin credentials.");
    }
  }

  async function handleEscalate() {
    setEscalateMsg(null);
    try {
      await onSendToAdmin();
    } catch {
      setEscalateMsg("Could not reach the server. Check API URL in Settings.");
    }
  }

  return (
    <div className="riskBlockOverlay" role="region" aria-labelledby="riskBlockTitle">
      <div className="riskBlockModal riskBlockModal--strip">
        <div className="riskBlockStripCol riskBlockStripCol--msg">
          <div className="riskBlockModalHeader riskBlockModalHeader--compact">
            <h2 id="riskBlockTitle" className="riskBlockTitle">
              Prompt blocked
            </h2>
            <p className="riskBlockLead">
              Risk high — admin access required to bypass prompt.
            </p>
          </div>
          <div className="riskBlockPromptBox riskBlockPromptBox--strip">
            <div className="riskBlockPromptLabel">Blocked prompt</div>
            <div className="riskBlockPromptText" title={promptPreview || ""}>
              {promptPreview || "—"}
            </div>
          </div>
        </div>

        <form
          className="riskBlockStripCol riskBlockStripCol--form"
          onSubmit={handleApprove}
        >
          <div className="riskBlockInputsRow">
            <label className="field riskBlockField riskBlockField--inline">
              <span>Admin ID</span>
              <input
                type="text"
                autoComplete="username"
                value={adminId}
                onChange={(e) => setAdminId(e.target.value)}
                placeholder="ID"
              />
            </label>
            <label className="field riskBlockField riskBlockField--inline">
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                placeholder="••••••••"
              />
            </label>
          </div>
          {approveError && <div className="riskBlockError">{approveError}</div>}
          <div className="riskBlockActions riskBlockActions--strip">
            <button
              type="button"
              className="btn btnGhost btnSm"
              onClick={onCancel}
              disabled={busyApprove}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btnPrimary btnSm"
              disabled={busyApprove || !adminId.trim() || !adminPassword}
            >
              {busyApprove ? "…" : "Approve"}
            </button>
          </div>
        </form>

        <div className="riskBlockStripCol riskBlockStripCol--aside">
          <button
            type="button"
            className="btn btnGhost btnSm riskBlockAsideBtn"
            onClick={() => void handleEscalate()}
            disabled={busyEscalate}
          >
            {busyEscalate ? "Sending…" : "Send to admin"}
          </button>
          {escalateMsg && <div className="riskBlockHint riskBlockHint--compact">{escalateMsg}</div>}
        </div>
      </div>
    </div>
  );
}
