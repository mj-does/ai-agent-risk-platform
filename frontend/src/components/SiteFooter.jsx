const COLS = [
  {
    title: "Resources",
    links: [
      ["Documentation", "#"],
      ["API reference", "#"],
      ["Attack log guide", "#"],
      ["Policy thresholds", "#"],
      ["Help center", "#"],
    ],
  },
  {
    title: "Product",
    links: [
      ["Control plane", "#"],
      ["Risk scoring", "#"],
      ["Session & LLM layers", "#"],
      ["TigerGraph logging", "#"],
    ],
  },
  {
    title: "Company",
    links: [
      ["About", "#"],
      ["Security", "#"],
      ["Terms", "#"],
      ["Privacy", "#"],
      ["Cookie settings", "#"],
    ],
  },
];

export default function SiteFooter() {
  return (
    <footer className="siteFooter" aria-label="Site footer">
      <div className="siteFooterInner">
        {COLS.map((col) => (
          <div key={col.title} className="siteFooterCol">
            <div className="siteFooterHeading">{col.title}</div>
            <ul className="siteFooterList">
              {col.links.map(([label, href]) => (
                <li key={label}>
                  <a href={href} className="siteFooterLink">
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </footer>
  );
}
