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
  className = "",
  view,
  onView,
  evaluations = [],
  selectedId,
  onSelect,
  onOpenSettings,
  onClose,
}) {
  const close = onClose || (() => {});

  return (
    <aside className={`sidebar ${className}`.trim()}>
      <div className="sidebarTop">
        <div className="sidebarBrand">
          <div className="brandMark">AR</div>
          <div>
            <div className="brandName">Access Risk</div>
            <div className="brandSub">Agent control plane</div>
          </div>
        </div>

        <nav className="nav">
          <NavItem
            active={view === "dashboard"}
            onClick={() => {
              onView("dashboard");
              close();
            }}
          >
            Control Plane
          </NavItem>
          <NavItem
            active={view === "evaluations"}
            onClick={() => {
              onView("evaluations");
              close();
            }}
          >
            Attack Logs
          </NavItem>
          <NavItem
            active={view === "policies"}
            onClick={() => {
              onView("policies");
              close();
            }}
          >
            Policy
          </NavItem>
          <NavItem
            active={false}
            onClick={() => {
              onOpenSettings();
              close();
            }}
          >
            Settings
          </NavItem>
        </nav>
      </div>

      <div className="sidebarSection">
        <div className="sidebarSectionHeader">
          <span>Recent attack logs</span>
          <Badge tone="neutral">{evaluations.length}</Badge>
        </div>

        {evaluations.length === 0 ? (
          <div className="sidebarEmpty">
            No evaluations yet. Simulate an attack or evaluate a prompt.
          </div>
        ) : (
          <div className="sidebarList">
            {evaluations.slice(0, 30).map((e) => {
              const rpct = Math.round((e.riskScore || 0) * 100);
              const tier =
                rpct >= 80 ? "high" : rpct >= 40 ? "mid" : "low";
              return (
              <button
                key={e.id}
                type="button"
                className={`sideRow sideRow--risk${tier} ${e.id === selectedId ? "sideRowActive" : ""}`}
                onClick={() => {
                  onSelect(e.id);
                  onView("dashboard");
                  close();
                }}
                title={e.prompt}
              >
                <div className="sideRowTop">
                  <div className="sideRowLeft">
                    <span className="sideRowTime">
                      {new Date(e.createdAt).toLocaleString()}
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
                    {((e.riskScore || 0) * 100).toFixed(1)}%
                  </Badge>
                </div>
                <div className="sideRowPrompt">{e.prompt}</div>
              </button>
            );
            })}
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