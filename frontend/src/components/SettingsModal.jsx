import { useEffect, useMemo, useState } from "react";
import { getApiBaseUrl, setApiBaseUrl } from "../api";

export default function SettingsModal({ onClose }) {
  const current = useMemo(() => getApiBaseUrl(), []);
  const [apiUrl, setApiUrl] = useState(current);

  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === "Escape") onClose?.();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  function save() {
    setApiBaseUrl(apiUrl);
    onClose?.();
  }

  return (
    <div className="modalOverlay" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modalHeader">
          <div>
            <div className="modalTitle">Settings</div>
            <div className="modalSub">Configure how the frontend connects to your backend.</div>
          </div>
          <button className="iconBtn" type="button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="modalBody">
          <label className="field">
            <span>Backend base URL</span>
            <input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://127.0.0.1:8080"
            />
          </label>
          <div className="helpText">
            Must match the port where <span className="mono">uvicorn</span> runs (e.g.{" "}
            <span className="mono">:8080</span> if 8000 is blocked). You can also set{" "}
            <span className="mono">VITE_API_URL</span> in <span className="mono">frontend/.env.development</span>{" "}
            and restart <span className="mono">npm run dev</span>.
          </div>
        </div>

        <div className="modalFooter">
          <button className="btn btnGhost" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btnPrimary" type="button" onClick={save}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

