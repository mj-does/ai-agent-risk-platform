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
              placeholder="http://127.0.0.1:8000"
            />
          </label>
          <div className="helpText">
            Tip: you can also set <span className="mono">VITE_API_URL</span> in your environment.
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

