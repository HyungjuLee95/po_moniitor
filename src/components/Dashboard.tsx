"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../api/client";
import { navigationFor } from "../config/navigation";
import type {
  Bootstrap,
  ChannelRow,
  MonitoringSummary,
  PoServer,
  User,
  ViewId,
} from "../types";

const emptySummary: MonitoringSummary = {
  sid: "",
  server_name: "",
  channels: { total: 0, running: 0, error: 0, stopped: 0 },
  messages_today: 0,
  success_rate: 0,
  average_latency_ms: 0,
  source: "loading",
};

export function Dashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [view, setView] = useState<ViewId>("overview");
  const [servers, setServers] = useState<PoServer[]>([]);
  const [selectedSid, setSelectedSid] = useState("");
  const [summary, setSummary] = useState(emptySummary);
  const [channels, setChannels] = useState<ChannelRow[]>([]);
  const [notice, setNotice] = useState("설정을 불러오는 중입니다.");
  const nav = useMemo(() => navigationFor(user.role), [user.role]);

  useEffect(() => {
    apiFetch<Bootstrap>("/configuration/bootstrap")
      .then((payload) => {
        setServers(payload.servers);
        setSelectedSid(payload.servers[0]?.sid ?? "");
        setNotice(`${payload.application.name} ${payload.application.version} · ${payload.application.mode.toUpperCase()}`);
      })
      .catch(() => setNotice("백엔드 설정을 불러오지 못했습니다."));
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
        setNotice(`${selectedSid} 서버와 동기화되었습니다.`);
      })
      .catch(() => setNotice(`${selectedSid} 서버 데이터를 불러오지 못했습니다.`));
  }, [selectedSid]);

  const activeServer = servers.find((server) => server.sid === selectedSid);
  const activeView = nav.find((item) => item.id === view);

  return (
    <main className="app">
      <aside className="sidebar">
        <div className="brand"><span>PO</span><div><b>MONITOR MAIN</b><small>Integration Operations</small></div></div>
        <nav aria-label="도메인 메뉴">
          <p>OPERATIONS</p>
          {nav.map((item) => (
            <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => setView(item.id)}>
              <span>{item.shortLabel}</span>{item.label}
            </button>
          ))}
        </nav>
        <div className="api-health"><span /><div><b>API CONNECTED</b><small>{notice}</small></div></div>
        <button className="account" onClick={onLogout} title="로그아웃">
          <span>{user.username.slice(0, 2).toUpperCase()}</span>
          <div><b>{user.display_name}</b><small>{user.role}</small></div>
          <i>↪</i>
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div><p>SAP PO OPERATIONS</p><h1>{activeView?.label ?? "운영 현황"}</h1></div>
          <div className="top-actions">
            <label className="server-select">
              <span className={`environment-dot ${activeServer?.environment ?? ""}`} />
              <select value={selectedSid} onChange={(event) => setSelectedSid(event.target.value)} aria-label="SAP PO 서버">
                {servers.map((server) => <option key={server.sid} value={server.sid}>{server.display_name} · {server.sid}</option>)}
              </select>
            </label>
            <button className="notification" aria-label="알림">3</button>
          </div>
        </header>

        <div className="content">
          <section className="context-bar">
            <div><span className="live-dot" /><b>{activeServer?.display_name || "서버 대기"}</b><small>{activeServer?.environment || "configuration"}</small></div>
            <p>{notice}</p>
          </section>

          {view === "overview" || view === "channels" ? (
            <>
              <section className="metrics">
                <Metric label="전체 채널" value={summary.channels.total.toLocaleString()} note={`${summary.channels.running} running`} tone="blue" />
                <Metric label="오늘 메시지" value={summary.messages_today.toLocaleString()} note={`${summary.success_rate}% success`} tone="green" />
                <Metric label="오류 채널" value={summary.channels.error.toLocaleString()} note={`${summary.channels.stopped} stopped`} tone="red" />
                <Metric label="평균 응답" value={`${summary.average_latency_ms}ms`} note={summary.source.toUpperCase()} tone="purple" />
              </section>

              <section className="dashboard-grid">
                <article className="panel throughput">
                  <div className="panel-head"><div><p>MESSAGE THROUGHPUT</p><h2>시간대별 처리 흐름</h2></div><span>최근 24시간</span></div>
                  <div className="bar-chart" aria-label="시간대별 메시지 처리량">
                    {[34, 49, 44, 67, 58, 76, 65, 83, 72, 91, 78, 86, 68, 74, 61, 80].map((height, index) => <i key={index} style={{ height: `${height}%` }} />)}
                  </div>
                  <div className="chart-caption"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span></div>
                </article>
                <article className="panel server-card">
                  <div className="panel-head"><div><p>SERVER PROFILE</p><h2>{activeServer?.sid || "—"}</h2></div><span className="status-badge">ONLINE</span></div>
                  <dl>
                    <div><dt>표시 이름</dt><dd>{activeServer?.display_name || "—"}</dd></div>
                    <div><dt>환경</dt><dd>{activeServer?.environment || "—"}</dd></div>
                    <div><dt>기능</dt><dd>{activeServer?.capabilities.join(", ") || "—"}</dd></div>
                    <div><dt>설정 원본</dt><dd>PO_SERVERS_JSON</dd></div>
                  </dl>
                </article>
              </section>

              <section className="panel channel-panel">
                <div className="panel-head"><div><p>CHANNEL HEALTH</p><h2>{selectedSid} 채널 상태</h2></div><button>새로고침</button></div>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>채널</th><th>컴포넌트</th><th>방향</th><th>상태</th><th>응답</th></tr></thead>
                    <tbody>
                      {channels.map((channel) => (
                        <tr key={channel.id}>
                          <td><b>{channel.channel_id}</b><small>{channel.sid}</small></td>
                          <td>{channel.component_id}</td><td>{channel.direction}</td>
                          <td><Status value={channel.status} /></td>
                          <td>{channel.latency_ms == null ? "—" : `${channel.latency_ms}ms`}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          ) : (
            <section className="panel domain-placeholder">
              <p>DOMAIN MODULE</p><h2>{activeView?.label}</h2>
              <p>{selectedSid} 서버를 기준으로 API 계약이 준비되어 있습니다. 해당 도메인의 `MANUAL.md`, `SKILL.md`, `ERRORS.md`를 기준으로 기능을 확장합니다.</p>
              <code>/api/v1/{view}</code>
            </section>
          )}
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value, note, tone }: { label: string; value: string; note: string; tone: string }) {
  return <article className={`metric ${tone}`}><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;
}

function Status({ value }: { value: ChannelRow["status"] }) {
  return <span className={`channel-status ${value.toLowerCase()}`}><i />{value}</span>;
}
