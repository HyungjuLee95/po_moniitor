"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import type { AuditEntry, ChannelInventoryRow, ChannelMessage } from "../../core/types";


export function MessagesPage({ sid, auditOnly = false }: { sid: string; auditOnly?: boolean }) {
  const [channels, setChannels] = useState<ChannelInventoryRow[]>([]);
  const [channelQuery, setChannelQuery] = useState("");
  const [selectedChannel, setSelectedChannel] = useState("");
  const [messages, setMessages] = useState<ChannelMessage[]>([]);
  const [messageId, setMessageId] = useState("");
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (auditOnly) return;
    const timer = window.setTimeout(() => {
      apiFetch<{ data: ChannelInventoryRow[] }>(`/channels/inventory?sid=${encodeURIComponent(sid)}&component_id=*&channel_pattern=*`)
        .then((payload) => setChannels(payload.data))
        .catch(() => setNotice("채널 목록을 불러오지 못했습니다."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [auditOnly, sid]);

  const filteredChannels = useMemo(() => {
    const normalized = channelQuery.trim().toLowerCase();
    if (!normalized) return channels.slice(0, 12);
    return channels.filter((channel) => (
      channel.channel_id.toLowerCase().includes(normalized)
      || channel.component_id.toLowerCase().includes(normalized)
    )).slice(0, 30);
  }, [channelQuery, channels]);

  const loadChannelMessages = async (channelId: string) => {
    setSelectedChannel(channelId);
    setChannelQuery(channelId);
    setLoading(true);
    setNotice("");
    setAudit([]);
    setMessageId("");
    try {
      const payload = await apiFetch<{ data: ChannelMessage[] }>(
        `/channels/message-history?sid=${encodeURIComponent(sid)}&channel_id=${encodeURIComponent(channelId)}&limit=100&offset=0`,
      );
      setMessages(payload.data);
      if (!payload.data.length) setNotice("선택한 채널에 조회된 메시지가 없습니다.");
    } catch {
      setMessages([]);
      setNotice("채널 메시지 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const loadAudit = async (id: string) => {
    const normalized = id.trim();
    if (!normalized) return;
    setMessageId(normalized);
    setLoading(true);
    setNotice("");
    try {
      const payload = await apiFetch<{ data: AuditEntry[] }>(`/messages/${encodeURIComponent(normalized)}/audit?sid=${encodeURIComponent(sid)}`);
      setAudit(payload.data);
      if (!payload.data.length) setNotice("조회된 Audit 로그가 없습니다.");
    } catch {
      setAudit([]);
      setNotice("Audit 조회에 실패했습니다. Message ID와 서버를 확인하세요.");
    } finally {
      setLoading(false);
    }
  };

  const submitAudit = (event: FormEvent) => {
    event.preventDefault();
    void loadAudit(messageId);
  };

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div>
          <p className="kicker">{auditOnly ? "MESSAGE AUDIT" : "CHANNEL MESSAGE TRACKING"}</p>
          <h2>{auditOnly ? "Message ID Audit 로그" : "채널별 메시지 추적"}</h2>
          <p>{auditOnly ? `${sid} 서버의 Message ID를 직접 조회합니다.` : "채널을 검색하고 메시지를 선택하면 해당 Message ID의 Audit 로그가 열립니다."}</p>
        </div>
      </header>

      {auditOnly ? (
        <form className="audit-search" onSubmit={submitAudit}>
          <label><span>Message ID</span><input value={messageId} onChange={(event) => setMessageId(event.target.value)} placeholder="Message ID를 입력하세요" /></label>
          <button className="primary-button" disabled={loading || !messageId.trim()}>Audit 조회</button>
        </form>
      ) : (
        <>
          <div className="channel-message-search">
            <label className="search-field"><span>채널 검색</span><input value={channelQuery} onChange={(event) => setChannelQuery(event.target.value)} placeholder="채널명 또는 등록 시스템" /></label>
            {channelQuery && <button className="secondary-button" onClick={() => setChannelQuery("")}>초기화</button>}
          </div>
          <div className="channel-search-results">
            {filteredChannels.map((channel) => (
              <button className={selectedChannel === channel.channel_id ? "active" : ""} key={`${channel.component_id}-${channel.channel_id}`} onClick={() => void loadChannelMessages(channel.channel_id)}>
                <b>{channel.channel_id}</b><small>{channel.component_id}</small>
              </button>
            ))}
            {!filteredChannels.length && <p>검색 결과가 없습니다.</p>}
          </div>
        </>
      )}

      {notice && <p className="inline-notice">{notice}</p>}
      <div className={`feature-split ${auditOnly ? "audit-only" : ""}`}>
        {!auditOnly && (
          <div className="table-card">
            <div className="table-caption"><b>{selectedChannel || "채널을 먼저 선택하세요"}</b><span>{messages.length} messages</span></div>
            <div className="data-table channel-message-table">
              <div className="data-row data-head"><span>Message ID</span><span>시각</span><span>응답</span><span>상태</span><span /></div>
              {messages.map((message) => (
                <div className={`data-row ${messageId === message.message_id ? "selected" : ""}`} key={message.log_id}>
                  <span><b>{message.message_id}</b><small>LOG {message.log_id}</small></span>
                  <span>{message.start_time ? new Date(message.start_time).toLocaleString("ko-KR") : "—"}</span>
                  <span>{message.elapsed_sec.toFixed(3)}초</span>
                  <span><i className={`status-pill ${message.status === "F" ? "error" : "running"}`}>{message.status}</i></span>
                  <span><button className="row-action" onClick={() => void loadAudit(message.message_id)}>Audit</button></span>
                </div>
              ))}
              {!loading && !messages.length && <p className="empty-state">채널을 선택하면 최근 메시지 목록이 표시됩니다.</p>}
            </div>
          </div>
        )}

        <aside className="detail-card audit-timeline">
          <p className="kicker">AUDIT TIMELINE</p>
          <h3>{messageId || "메시지를 선택하세요"}</h3>
          {audit.map((entry, index) => (
            <article key={`${entry.time}-${index}`}>
              <i />
              <div><b>{entry.status || "INFO"}</b><small>{entry.time ? new Date(entry.time).toLocaleString("ko-KR") : "—"}</small><p>{entry.text || "내용 없음"}</p></div>
            </article>
          ))}
          {!audit.length && <div className="detail-empty"><span>≡</span><b>Audit 대기</b><p>{auditOnly ? "Message ID를 입력하세요." : "왼쪽 메시지 목록에서 Audit을 선택하세요."}</p></div>}
        </aside>
      </div>
    </section>
  );
}
