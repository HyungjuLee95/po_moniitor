"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import { navigationFor } from "../../core/navigation";
import type { Bootstrap, ChannelRow, MonitoringSummary, PoServer, User, ViewId } from "../../core/types";
import { AlertDrawer } from "../alerts/AlertDrawer";
import { IncidentWatchWidget } from "../alerts/IncidentWatchWidget";
import { mockAlerts } from "../alerts/mockAlerts";
import { ChannelStatusWidget } from "../channels/ChannelStatusWidget";
import { HealthMetrics, ThroughputWidget } from "../monitoring/MonitoringWidgets";
import { ServerProfileWidget } from "../server/ServerProfileWidget";
import { DashboardEditor } from "./DashboardEditor";
import { fallbackChannels, fallbackServers, fallbackSummary } from "./mockData";
import type { WidgetId } from "./types";
import { useDashboardLayout } from "./useDashboardLayout";

export function OperationsWorkspace({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [view, setView] = useState<ViewId>("overview");
  const [servers, setServers] = useState<PoServer[]>(fallbackServers);
  const [selectedSid, setSelectedSid] = useState(fallbackServers[0].sid);
  const [summary, setSummary] = useState<MonitoringSummary>(fallbackSummary);
  const [channels, setChannels] = useState<ChannelRow[]>(fallbackChannels);
  const [connected, setConnected] = useState(false);
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const dashboard = useDashboardLayout();
  const nav = useMemo(() => navigationFor(user.role), [user.role]);

  useEffect(() => {
    apiFetch<Bootstrap>("/configuration/bootstrap")
      .then((payload) => {
        if (payload.servers.length) {
          setServers(payload.servers);
          setSelectedSid(payload.servers[0].sid);
        }
        setConnected(true);
      })
      .catch(() => setConnected(false));
  }, []);

  useEffect(() => {
    if (!selectedSid) return;
    Promise.all([
      apiFetch<{ data: MonitoringSummary }>(`/monitoring/summary?sid=${encodeURIComponent(selectedSid)}`),
      apiFetch<{ data: ChannelRow[] }>(`/channels?sid=${encodeURIComponent(selectedSid)}`),
    ])
      .then(([summaryPayload, channelPayload]) => {
        setSummary(summaryPayload.data);
        setChannels(channelPayload.data);
        setConnected(true);
      })
      .catch(() => {
        setSummary({ ...fallbackSummary, sid: selectedSid, server_name: servers.find((server) => server.sid === selectedSid)?.display_name ?? selectedSid });
        setChannels(fallbackChannels.map((channel) => ({ ...channel, sid: selectedSid })));
      });
  }, [selectedSid, servers]);

  useEffect(() => {
    if (!navigationOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setNavigationOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [navigationOpen]);

  const activeServer = servers.find((server) => server.sid === selectedSid);
  const activeNavigation = nav.find((item) => item.id === view) ?? nav[0];
  const openAlerts = mockAlerts.filter((alert) => alert.status === "open");
  const criticalCount = openAlerts.filter((alert) => alert.severity === "critical").length;

  const renderWidget = (widgetId: WidgetId) => {
    if (dashboard.layout.hidden.includes(widgetId)) return null;

    switch (widgetId) {
      case "health":
        return <HealthMetrics summary={summary} key={widgetId} />;
      case "throughput":
        return <ThroughputWidget key={widgetId} />;
      case "server_profile":
        return <ServerProfileWidget server={activeServer} connected={connected} key={widgetId} />;
      case "channel_status":
        return <ChannelStatusWidget channels={channels} key={widgetId} />;
      case "incidents":
        return <IncidentWatchWidget alerts={openAlerts} onOpen={() => setAlertsOpen(true)} key={widgetId} />;
    }
  };

  return (
    <main className={`console-shell density-${dashboard.layout.density}`}>
      <aside id="primary-navigation" className={`side-navigation ${navigationOpen ? "open" : ""}`}>
        <div className="brand-lockup">
          <span className="brand-symbol">PO</span>
          <div><b>MONITOR MAIN</b><small>OPERATIONS CONSOLE</small></div>
          <button className="navigation-close" onClick={() => setNavigationOpen(false)} aria-label="메뉴 닫기">×</button>
        </div>
        <nav aria-label="주 메뉴">
          <p className="nav-caption">WORKSPACE</p>
          {nav.map((item) => (
            <button key={item.id} className={item.id === view ? "active" : ""} onClick={() => { setView(item.id); setNavigationOpen(false); }}>
              <span>{item.glyph}</span>
              <div><small>{item.eyebrow}</small><b>{item.label}</b></div>
            </button>
          ))}
        </nav>
        <div className={`connection-card ${connected ? "connected" : ""}`}>
          <i />
          <div><b>{connected ? "API CONNECTED" : "PREVIEW MODE"}</b><small>{connected ? "실시간 동기화 중" : "백엔드 연결 대기"}</small></div>
        </div>
        <button className="user-card" onClick={onLogout}>
          <span>{user.display_name.slice(0, 1)}</span>
          <div><b>{user.display_name}</b><small>{user.role}</small></div>
          <em>로그아웃</em>
        </button>
      </aside>

      <section className="console-main">
        <header className="console-topbar">
          <div className="topbar-identity">
            <button
              className="menu-button"
              onClick={() => setNavigationOpen(true)}
              aria-controls="primary-navigation"
              aria-expanded={navigationOpen}
              aria-label="주 메뉴 열기"
            >
              <span /><span /><span />
            </button>
            <div>
            <p className="breadcrumb">PO MONITOR / {activeNavigation.eyebrow}</p>
            <h1>{activeNavigation.label}</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <label className="server-switcher">
              <i className={activeServer?.environment ?? ""} />
              <span><small>ACTIVE SERVER</small>
                <select value={selectedSid} onChange={(event) => setSelectedSid(event.target.value)} aria-label="SAP PO 서버 선택">
                  {servers.map((server) => <option key={server.sid} value={server.sid}>{server.display_name} · {server.sid}</option>)}
                </select>
              </span>
            </label>
            <button className="customize-button" onClick={() => setEditorOpen(true)}><span>+</span> 대시보드 편집</button>
            <button className={`alert-button ${criticalCount ? "has-critical" : ""}`} onClick={() => setAlertsOpen(true)} aria-label={`알림 ${openAlerts.length}건`}>
              <i />
              {openAlerts.length > 0 && <b>{openAlerts.length}</b>}
            </button>
          </div>
        </header>

        <div className="workspace-content">
          <section className="welcome-row">
            <div>
              <p className="kicker">{new Date().toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric", weekday: "long" })}</p>
              <h2>{user.display_name}님, 운영 흐름을 확인하세요.</h2>
              <p>{activeServer?.display_name} 기준으로 최신 상태를 보여드립니다.</p>
            </div>
            <div className="live-clock"><i /><span><b>LIVE</b><small>30초마다 자동 갱신</small></span></div>
          </section>

          {view === "overview" ? (
            <section className="dashboard-canvas">
              {dashboard.layout.order.map(renderWidget)}
            </section>
          ) : (
            <section className="surface domain-stage">
              <p className="kicker">{activeNavigation.eyebrow} DOMAIN</p>
              <h2>{activeNavigation.label}</h2>
              <p>{selectedSid} 서버를 기준으로 기능이 연결될 영역입니다. 해당 도메인의 README, MANUAL, SKILL, ERROR 문서를 기준으로 다음 기능을 확장합니다.</p>
              <code>/api/v1/{view}</code>
            </section>
          )}
        </div>
      </section>

      {navigationOpen && <button className="navigation-scrim" onClick={() => setNavigationOpen(false)} aria-label="메뉴 닫기" />}
      {editorOpen && (
        <>
          <button className="drawer-scrim" onClick={() => setEditorOpen(false)} aria-label="편집 닫기" />
          <DashboardEditor
            layout={dashboard.layout}
            saved={dashboard.saved}
            onToggle={dashboard.toggle}
            onMove={dashboard.move}
            onDensity={(density) => dashboard.setLayout({ ...dashboard.layout, density })}
            onReset={dashboard.reset}
            onSave={dashboard.save}
            onClose={() => setEditorOpen(false)}
          />
        </>
      )}
      <AlertDrawer alerts={mockAlerts} open={alertsOpen} onClose={() => setAlertsOpen(false)} />
    </main>
  );
}
