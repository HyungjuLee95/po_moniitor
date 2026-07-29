"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import type { MessageRow } from "../../core/types";

type StatusFilter = "" | "SUCCESS" | "FAILED" | "DELIVERING";

function statusClass(status: string): string {
  const normalized = status.toUpperCase();
  if (["F", "FAIL", "FAILED", "ERROR"].includes(normalized)) return "error";
  if (["P", "PENDING", "DELIVERING"].includes(normalized)) return "stopped";
  return "running";
}

export function RealtimeInterfacesPage({ sid }: { sid: string }) {
  const [rows, setRows] = useState<MessageRow[]>([]);
  const [status, setStatus] = useState<StatusFilter>("");
  const [keyword, setKeyword] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    if (!sid) return;
    setLoading(true);
    const params = new URLSearchParams({ sid, limit: "100", hours: "24" });
    if (status) params.set("status", status);
    if (keyword.trim()) params.set("keyword", keyword.trim());
    try {
      const payload = await apiFetch<{ data: MessageRow[] }>(`/messages?${params}`);
      setRows(payload.data);
      setLastUpdated(new Date());
      setNotice("");
    } catch {
      setRows([]);
      setNotice("실시간 인터페이스 내역을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [keyword, sid, status]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = window.setInterval(() => void load(), 15_000);
    return () => window.clearInterval(timer);
  }, [autoRefresh, load]);

  const counts = useMemo(() => ({
    total: rows.length,
    failed: rows.filter((row) => statusClass(row.status) === "error").length,
    delivering: rows.filter((row) => statusClass(row.status) === "stopped").length,
  }), [rows]);

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div>
          <p className="kicker">REALTIME INTERFACE FLOW</p>
          <h2>실시간 인터페이스 내역</h2>
          <p>RTIMS 최근 메시지를 15초 간격으로 갱신하고 상태·인터페이스 기준으로 좁혀봅니다.</p>
        </div>
        <div className="live-controls">
          <label><input type="checkbox" checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} /> 자동 갱신</label>
          <button className="secondary-button" onClick={() => void load()} disabled={loading}>{loading ? "갱신 중…" : "지금 갱신"}</button>
        </div>
      </header>

      <div className="feature-toolbar wrap-toolbar">
        <label className="search-field"><span>인터페이스·시스템</span><input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="HRD, ERP, MES…" /></label>
        <label className="compact-select"><span>상태</span><select value={status} onChange={(event) => setStatus(event.target.value as StatusFilter)}><option value="">전체</option><option value="SUCCESS">성공</option><option value="FAILED">실패</option><option value="DELIVERING">Delivering</option></select></label>
        <button className="primary-button" onClick={() => void load()} disabled={loading}>조회</button>
      </div>

      <div className="inline-stat-strip">
        <span><small>조회</small><b>{counts.total}</b></span>
        <span><small>실패</small><b>{counts.failed}</b></span>
        <span><small>Delivering</small><b>{counts.delivering}</b></span>
        <em>{lastUpdated ? `${lastUpdated.toLocaleTimeString("ko-KR")} 갱신` : "조회 대기"}</em>
      </div>
      {notice && <p className="inline-notice">{notice}</p>}

      <div className="table-card">
        <div className="table-caption"><b>최근 인터페이스 메시지</b><span>{sid} · 최근 24시간</span></div>
        <div className="data-table realtime-message-table">
          <div className="data-row data-head"><span>시각</span><span>인터페이스</span><span>송신 → 수신</span><span>상태</span><span>Message ID</span></div>
          {rows.map((row) => (
            <details className="data-row expandable-row" key={row.message_id}>
              <summary>
                <span>{row.start_time ? new Date(row.start_time).toLocaleString("ko-KR") : "—"}</span>
                <span><b>{row.interface_name || "미확인"}</b></span>
                <span>{row.source_system || "—"} → {row.target_system || "—"}</span>
                <span><i className={`status-pill ${statusClass(row.status)}`}>{row.status}</i></span>
                <span>{row.message_id}</span>
              </summary>
              <div className="expandable-content">
                <span><b>처리시간</b>{row.duration_ms == null ? "—" : `${(row.duration_ms / 1000).toFixed(3)}초`}</span>
                <span><b>Namespace</b>{row.namespace || "—"}</span>
                <span><b>오류</b>{row.error_text || "없음"}</span>
              </div>
            </details>
          ))}
          {!loading && !rows.length && <p className="empty-state">조건에 맞는 인터페이스 메시지가 없습니다.</p>}
        </div>
      </div>
    </section>
  );
}
