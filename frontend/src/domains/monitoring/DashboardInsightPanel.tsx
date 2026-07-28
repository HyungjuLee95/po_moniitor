"use client";

import type { ChannelRow, MonitoringPolicy, SlowMessage } from "../../core/types";
import type { AlertItem } from "../alerts/types";


export function DashboardInsightPanel({
  mode,
  channels,
  alerts,
  slowMessages,
  policy,
  loading,
}: {
  mode: "issues" | "latency" | null;
  channels: ChannelRow[];
  alerts: AlertItem[];
  slowMessages: SlowMessage[];
  policy: MonitoringPolicy | null;
  loading: boolean;
}) {
  if (!mode) return null;
  const problemChannels = channels.filter((channel) => channel.status !== "Running");

  return (
    <section className={`surface dashboard-insight ${mode}`}>
      <header>
        <div>
          <p className="kicker">{mode === "issues" ? "ACTION REQUIRED" : "RESPONSE INSIGHT"}</p>
          <h3>{mode === "issues" ? "확인이 필요한 운영 항목" : "응답 지연 메시지"}</h3>
        </div>
        {mode === "latency" && policy && (
          <span className="insight-rule">최근 {policy.response_window_minutes}분 · {(policy.slow_threshold_ms / 1000).toFixed(3)}초 이상</span>
        )}
      </header>

      {mode === "issues" ? (
        <div className="insight-columns">
          <details open>
            <summary><b>오류·중지 채널</b><span>{problemChannels.length}건</span></summary>
            <div className="insight-list">
              {problemChannels.map((channel) => (
                <details key={channel.id}>
                  <summary><span><i className={`status-dot ${channel.status.toLowerCase()}`} />{channel.channel_id}</span><b>{channel.status}</b></summary>
                  <dl><div><dt>시스템</dt><dd>{channel.component_id}</dd></div><div><dt>방향</dt><dd>{channel.direction}</dd></div><div><dt>응답</dt><dd>{channel.latency_ms == null ? "—" : `${(channel.latency_ms / 1000).toFixed(3)}초`}</dd></div></dl>
                </details>
              ))}
              {!problemChannels.length && <p>오류 또는 중지 채널이 없습니다.</p>}
            </div>
          </details>
          <details open>
            <summary><b>열린 오류 메시지</b><span>{alerts.length}건</span></summary>
            <div className="insight-list">
              {alerts.map((alert) => (
                <details key={alert.id}>
                  <summary><span><i className={`status-dot ${alert.severity}`} />{alert.title}</span><b>{alert.sid}</b></summary>
                  <p>{alert.detail}</p>
                  <small>{alert.domain} · {alert.occurredAt}</small>
                </details>
              ))}
              {!alerts.length && <p>열린 오류 메시지가 없습니다.</p>}
            </div>
          </details>
        </div>
      ) : (
        <div className="insight-list slow-message-list">
          {loading && <p>응답 지연 메시지를 불러오는 중입니다.</p>}
          {!loading && slowMessages.map((message) => (
            <details key={message.log_id}>
              <summary>
                <span><i className={`status-dot ${message.status === "F" ? "error" : "warning"}`} />{message.interface_name || message.message_id}</span>
                <b>{message.elapsed_sec.toFixed(3)}초</b>
              </summary>
              <dl>
                <div><dt>Message ID</dt><dd>{message.message_id}</dd></div>
                <div><dt>시스템 흐름</dt><dd>{message.source_system || "—"} → {message.target_system || "—"}</dd></div>
                <div><dt>상태</dt><dd>{message.status}</dd></div>
                <div><dt>시작 시각</dt><dd>{message.start_time ? new Date(message.start_time).toLocaleString("ko-KR") : "—"}</dd></div>
              </dl>
            </details>
          ))}
          {!loading && !slowMessages.length && <p>설정된 기준을 초과한 메시지가 없습니다.</p>}
        </div>
      )}
    </section>
  );
}
