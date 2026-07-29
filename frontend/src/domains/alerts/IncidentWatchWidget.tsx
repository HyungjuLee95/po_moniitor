import { PanelHeader } from "../dashboard/PanelHeader";
import type { AlertItem } from "./types";

export function IncidentWatchWidget({ alerts, loading, onOpen }: { alerts: AlertItem[]; loading: boolean; onOpen: () => void }) {
  return (
    <article className="surface incident-card">
      <PanelHeader eyebrow="INCIDENT WATCH" title="최근 장애" action={`${alerts.length} open`} />
      <div className="compact-alerts">
        {loading && <p className="widget-loading">알림을 불러오는 중입니다.</p>}
        {!loading && alerts.map((alert) => (
          <button key={alert.id} onClick={onOpen}>
            <i className={alert.severity} />
            <span><b>{alert.title}</b><small>{alert.sid} · {alert.occurredAt}</small></span>
            <em>›</em>
          </button>
        ))}
      </div>
      <button className="panel-link" onClick={onOpen}>모든 알림 보기 <span>→</span></button>
    </article>
  );
}
