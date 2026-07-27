export function PanelHeader({ eyebrow, title, action }: { eyebrow: string; title: string; action: string }) {
  return <header className="panel-header"><div><p>{eyebrow}</p><h3>{title}</h3></div><span>{action}</span></header>;
}
