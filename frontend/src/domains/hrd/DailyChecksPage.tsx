"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import { DASHBOARD_REQUEST_TIMEOUT_MS } from "../../core/refresh";
import type { MessageRow } from "../../core/types";

type HrdCheckRow = {
  component_id: string;
  channel_id: string;
  if_id: string;
  table_name: string | null;
  batch_tm: string | null;
  company_cd: string[];
};

export function useDailyChecks(sid: string, refreshIntervalMs = 0) {
  const [hrdRows, setHrdRows] = useState<HrdCheckRow[]>([]);
  const [deliveringRows, setDeliveringRows] = useState<MessageRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (!sid) return;
    setLoading(true);
    const [hrdResult, deliveringResult] = await Promise.allSettled([
        apiFetch<{ data: HrdCheckRow[] }>(
          `/hrd/interfaces?sid=${encodeURIComponent(sid)}&search_ifid=HRD`,
          { timeoutMs: DASHBOARD_REQUEST_TIMEOUT_MS },
        )
          .then((payload) => setHrdRows(payload.data)),
        apiFetch<{ data: MessageRow[] }>(
          `/messages?sid=${encodeURIComponent(sid)}&limit=200&hours=168&status=DELIVERING`,
          { timeoutMs: DASHBOARD_REQUEST_TIMEOUT_MS },
        )
          .then((payload) => setDeliveringRows(payload.data)),
    ]);
    setNotice(
      hrdResult.status === "rejected" && deliveringResult.status === "rejected"
        ? "일일 점검 데이터를 불러오지 못했습니다."
        : hrdResult.status === "rejected"
          ? "이 서버는 HRD 조회 capability가 없거나 연결되지 않았습니다."
          : deliveringResult.status === "rejected"
            ? "Delivering 메시지 조회를 완료하지 못했습니다."
            : "",
    );
    setLoading(false);
  }, [sid]);

  useEffect(() => {
    const initialTimer = window.setTimeout(() => {
      setHrdRows([]);
      setDeliveringRows([]);
      void load();
    }, 0);
    const refreshTimer = refreshIntervalMs > 0
      ? window.setInterval(() => void load(), refreshIntervalMs)
      : undefined;
    return () => {
      window.clearTimeout(initialTimer);
      if (refreshTimer) window.clearInterval(refreshTimer);
    };
  }, [load, refreshIntervalMs]);

  return { hrdRows, deliveringRows, loading, notice, load };
}

export function DailyChecksPage({ sid }: { sid: string }) {
  const { hrdRows, deliveringRows, loading, notice, load } = useDailyChecks(sid);

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div>
          <p className="kicker">DAILY OPERATIONS CHECK</p>
          <h2>HRD·Delivering 일일 점검</h2>
          <p>자주 확인하는 HRD 인터페이스 현행과 최근 7일 Delivering 메시지를 한 번에 조회합니다.</p>
        </div>
        <button className="secondary-button" onClick={() => void load()} disabled={loading}>{loading ? "점검 중…" : "다시 점검"}</button>
      </header>
      <div className="daily-check-summary">
        <article><small>HRD 인터페이스 현행</small><strong>{hrdRows.length}</strong><span>HRD 키워드</span></article>
        <article className={deliveringRows.length ? "attention" : ""}><small>Delivering 메시지</small><strong>{deliveringRows.length}</strong><span>최근 7일</span></article>
      </div>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="feature-split daily-check-grid">
        <div className="table-card">
          <div className="table-caption"><b>HRD 인터페이스 현행</b><span>{hrdRows.length} interfaces</span></div>
          <div className="data-table daily-hrd-table">
            <div className="data-row data-head"><span>I/F ID</span><span>Table</span><span>Company</span><span>Batch</span></div>
            {hrdRows.map((row) => <div className="data-row" key={`${row.component_id}|${row.channel_id}`}><span><b>{row.if_id}</b><small>{row.channel_id}</small></span><span>{row.table_name || "—"}</span><span>{row.company_cd.join(", ") || "—"}</span><span>{row.batch_tm || "수동/미정의"}</span></div>)}
          </div>
        </div>
        <div className="table-card">
          <div className="table-caption"><b>7일 Delivering</b><span>{deliveringRows.length} messages</span></div>
          <div className="data-table daily-message-table">
            <div className="data-row data-head"><span>인터페이스</span><span>시각</span><span>Message ID</span></div>
            {deliveringRows.map((row) => <div className="data-row" key={row.message_id}><span><b>{row.interface_name || "미확인"}</b><small>{row.source_system || "—"} → {row.target_system || "—"}</small></span><span>{row.start_time ? new Date(row.start_time).toLocaleString("ko-KR") : "—"}</span><span>{row.message_id}</span></div>)}
          </div>
        </div>
      </div>
    </section>
  );
}
