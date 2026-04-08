import Badge from "./Badge";

function NavItem({ active, children, onClick }) {
  return (
    <button
      type="button"
      className={`navItem ${active ? "navItemActive" : ""}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function Sidebar({
  view,
  onView,
  evaluations = [],
  selectedId,
  onSelect,
  onOpenSettings,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebarTop">
        <div className="sidebarBrand">
          <div className="brandMark">AR</div>
          <div>
            <div className="brandName">Access Risk</div>
            <div className="brandSub">Agent control plane</div>
          </div>
        </div>

        <nav className="nav">
          <NavItem active={view === "dashboard"} onClick={() => onView("dashboard")}>
            Dashboard
          </NavItem>
          <NavItem
            active={view === "evaluations"}
            onClick={() => onView("evaluations")}
          >
            Evaluations
          </NavItem>
          <NavItem active={view === "policies"} onClick={() => onView("policies")}>
            Policy
          </NavItem>
          <NavItem active={false} onClick={onOpenSettings}>
            Settings
          </NavItem>
        </nav>
      </div>

      <div className="sidebarSection">
        <div className="sidebarSectionHeader">
          <span>Recent evaluations</span>
          <Badge tone="neutral">{evaluations.length}</Badge>
        </div>

        {evaluations.length === 0 ? (
          <div className="sidebarEmpty">
            No evaluations yet. Run the demo or evaluate a prompt.
          </div>
        ) : (
          <div className="sidebarList">
            {evaluations.slice(0, 30).map((e) => (
              <button
                key={e.id}
                type="button"
                className={`sideRow ${e.id === selectedId ? "sideRowActive" : ""}`}
                onClick={() => {
                  onSelect(e.id);
                  onView("dashboard");
                }}
                title={e.prompt}
              >
                <div className="sideRowTop">
                  <div className="sideRowLeft">
                    <span className="sideRowAgent">{e.agentName}</span>
                    <span className="sideRowTime">
                      {new Date(e.createdAt).toLocaleTimeString()}
                    </span>
                  </div>
                  <Badge
                    tone={
                      e.decision === "BLOCK"
                        ? "danger"
                        : e.decision === "REVIEW"
                          ? "warning"
                          : "success"
                    }
                  >
                    {Math.round((e.riskScore || 0) * 100)}%
                  </Badge>
                </div>
                <div className="sideRowPrompt">{e.prompt}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="sidebarFooter">
        <div className="footerHint">
          Decisions are policy-driven and auditable.
        </div>
      </div>
    </aside>
  );
}