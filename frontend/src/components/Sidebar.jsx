export default function Sidebar({ events = [], onSelect }) {
  return (
    <aside className="sidebar">
      <h3>Recent Prompts</h3>

      {events.length === 0 && (
        <p className="empty">No prompts yet</p>
      )}

      {events.map((e) => (
        <div
          key={e.id}
          className="event"
          onClick={() => onSelect(e)}
        >
          <p className="prompt">{e.prompt}</p>
          <span className="status">{e.status}</span>
        </div>
      ))}
    </aside>
  );
}