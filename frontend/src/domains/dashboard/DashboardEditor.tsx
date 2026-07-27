"use client";

import type { DashboardLayout, WidgetId } from "./types";
import { widgets } from "./widgetRegistry";

export function DashboardEditor({
  layout,
  saved,
  onToggle,
  onMove,
  onDensity,
  onReset,
  onSave,
  onClose,
}: {
  layout: DashboardLayout;
  saved: boolean;
  onToggle: (id: WidgetId) => void;
  onMove: (id: WidgetId, direction: -1 | 1) => void;
  onDensity: (density: DashboardLayout["density"]) => void;
  onReset: () => void;
  onSave: () => void;
  onClose: () => void;
}) {
  const ordered = layout.order.map((id) => widgets.find((widget) => widget.id === id)).filter(Boolean);

  return (
    <aside className="editor-panel">
      <header>
        <div><p className="kicker">PERSONALIZE</p><h2>대시보드 편집</h2></div>
        <button className="icon-button" onClick={onClose} aria-label="닫기">×</button>
      </header>
      <p className="editor-copy">내 업무에 필요한 위젯만 선택하고 표시 순서를 조정하세요.</p>
      <div className="density-control">
        <span>정보 밀도</span>
        <div>
          <button className={layout.density === "comfortable" ? "active" : ""} onClick={() => onDensity("comfortable")}>여유롭게</button>
          <button className={layout.density === "compact" ? "active" : ""} onClick={() => onDensity("compact")}>컴팩트</button>
        </div>
      </div>
      <div className="widget-editor-list">
        {ordered.map((widget, index) => widget && (
          <article key={widget.id}>
            <button className={`visibility-toggle ${layout.hidden.includes(widget.id) ? "" : "on"}`} onClick={() => onToggle(widget.id)} aria-label={`${widget.name} 표시 전환`}><i /></button>
            <div><b>{widget.name}</b><small>{widget.description}</small></div>
            <div className="order-buttons">
              <button disabled={index === 0} onClick={() => onMove(widget.id, -1)} aria-label="위로">↑</button>
              <button disabled={index === ordered.length - 1} onClick={() => onMove(widget.id, 1)} aria-label="아래로">↓</button>
            </div>
          </article>
        ))}
      </div>
      <footer>
        <button className="secondary-button" onClick={onReset}>기본값 복원</button>
        <button className="primary-button" onClick={onSave}>{saved ? "저장됨" : "설정 저장"}</button>
      </footer>
    </aside>
  );
}
