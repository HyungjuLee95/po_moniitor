"use client";

import { useState } from "react";

import { LlmSearchPanel } from "../llm_search/LlmSearchPanel";
import type { AlertItem } from "./types";

export function AlertDrawer({
  alerts,
  open,
  onClose,
}: {
  alerts: AlertItem[];
  open: boolean;
  onClose: () => void;
}) {
  const [selected, setSelected] = useState<AlertItem | null>(null);

  if (!open) return null;

  return (
    <>
      <button className="drawer-scrim" onClick={onClose} aria-label="알림 닫기" />
      <aside className="alert-drawer" aria-label="운영 알림">
        <header>
          <div><p className="kicker">OPERATIONS FEED</p><h2>실시간 알림</h2></div>
          <button className="icon-button" onClick={onClose} aria-label="닫기">×</button>
        </header>
        <div className="alert-summary">
          <strong>{alerts.filter((alert) => alert.status === "open").length}</strong>
          <span>확인이 필요한 알림</span>
          <button>모두 읽음 처리</button>
        </div>
        <div className="alert-list">
          {alerts.map((alert) => (
            <article className={`alert-row ${alert.severity}`} key={alert.id}>
              <div className="alert-row-head">
                <span className={`severity ${alert.severity}`}>{alert.severity}</span>
                <small>{alert.occurredAt}</small>
              </div>
              <h3>{alert.title}</h3>
              <p>{alert.detail}</p>
              <div className="alert-meta"><span>{alert.sid}</span><span>{alert.domain}</span><span>{alert.status}</span></div>
              <button className="text-button" onClick={() => setSelected(alert)}>LLM으로 원인 검색 <span>↗</span></button>
            </article>
          ))}
        </div>
      </aside>
      {selected && <LlmSearchPanel alert={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
