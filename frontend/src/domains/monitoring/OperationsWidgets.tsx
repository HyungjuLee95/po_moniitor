"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import { DASHBOARD_REFRESH_INTERVAL_MS, DASHBOARD_REQUEST_TIMEOUT_MS } from "../../core/refresh";
import type { MessageRow, ViewId } from "../../core/types";
import { useDailyChecks } from "../hrd/DailyChecksPage";
import { PanelHeader } from "../dashboard/PanelHeader";

type SystemResult = {
  group_id: number | null;
  system_name: string | null;
  success_count: number;
  fail_count: number;
  pending_count: number;
  total_count: number;
  success_rate: number;
};

type QueueData = {
  adapter_engine: Array<{
    servernode: string;
    queuename: string;
    started: string;
    num_entries: number;
    threads_working: number;
    max_thread: number;
  }>;
  integration_engine: Array<{
    client_id: string;
    direction: string;
    normal: number;
    warning: number;
    fail: number;
  }>;
};

export function SystemResultsWidget({ sid, onNavigate }: { sid: string; onNavigate: (view: ViewId) => void }) {
  const [rows, setRows] = useState<SystemResult[]>([]);
  const [filter, setFilter] = useState<"all" | "normal" | "error" | "delivering">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = (initial: boolean) => {
      if (initial) setLoading(true);
      void apiFetch<{ data: SystemResult[] }>(
        `/monitoring/system-statistics?sid=${encodeURIComponent(sid)}&hours=24`,
        { timeoutMs: DASHBOARD_REQUEST_TIMEOUT_MS },
      )
        .then((payload) => {
          if (!cancelled) setRows(payload.data);
        })
        .catch(() => {
          if (!cancelled && initial) setRows([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    };
    const initialTimer = window.setTimeout(() => load(true), 0);
    const refreshTimer = window.setInterval(() => load(false), DASHBOARD_REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(initialTimer);
      window.clearInterval(refreshTimer);
    };
  }, [sid]);

  const filtered = useMemo(() => rows.filter((row) => {
    if (filter === "normal") return row.fail_count === 0 && row.pending_count === 0;
    if (filter === "error") return row.fail_count > 0;
    if (filter === "delivering") return row.pending_count > 0;
    return true;
  }).slice(0, 7), [filter, rows]);

  return (
    <article className="surface system-result-widget span-two">
      <PanelHeader eyebrow="SYSTEM INTERFACE RESULT" title="시스템별 인터페이스 처리 결과" action="최근 24시간" />
      <div className="status-tabs" role="group" aria-label="시스템 처리 상태 필터">
        {([["all", "전체"], ["normal", "정상"], ["error", "오류"], ["delivering", "Delivering"]] as const).map(([id, label]) => <button className={filter === id ? "active" : ""} onClick={() => setFilter(id)} key={id}>{label}</button>)}
      </div>
      <div className="dashboard-result-table">
        <div className="dashboard-result-head"><span>시스템</span><span>전체</span><span>성공</span><span>실패</span><span>Delivering</span><span>성공률</span></div>
        {loading && !rows.length && <p className="widget-loading">시스템별 처리 결과를 불러오는 중입니다.</p>}
        {filtered.map((row, index) => <div key={`${row.group_id}|${index}`}><span><b>{row.system_name || "미분류"}</b></span><span>{row.total_count.toLocaleString()}</span><span>{row.success_count.toLocaleString()}</span><span className={row.fail_count ? "danger-text" : ""}>{row.fail_count.toLocaleString()}</span><span className={row.pending_count ? "warning-text" : ""}>{row.pending_count.toLocaleString()}</span><span>{row.success_rate.toFixed(2)}%</span></div>)}
        {!loading && !filtered.length && <p className="empty-state">선택한 상태의 시스템 결과가 없습니다.</p>}
      </div>
      <button className="text-button" onClick={() => onNavigate("system_status")}>전체 처리 결과 보기 <span>→</span></button>
    </article>
  );
}

export function QueueThreadWidget({ sid, onNavigate }: { sid: string; onNavigate: (view: ViewId) => void }) {
  const [queues, setQueues] = useState<QueueData>({ adapter_engine: [], integration_engine: [] });
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    const load = (initial: boolean) => {
      if (initial) setLoading(true);
      void apiFetch<{ data: QueueData }>(
        `/monitoring/queues?sid=${encodeURIComponent(sid)}`,
        { timeoutMs: DASHBOARD_REQUEST_TIMEOUT_MS },
      )
        .then((payload) => {
          if (!cancelled) setQueues(payload.data);
        })
        .catch(() => {
          if (!cancelled && initial) setQueues({ adapter_engine: [], integration_engine: [] });
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    };
    const initialTimer = window.setTimeout(() => load(true), 0);
    const refreshTimer = window.setInterval(() => load(false), DASHBOARD_REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(initialTimer);
      window.clearInterval(refreshTimer);
    };
  }, [sid]);
  const entries = queues.adapter_engine.reduce((sum, row) => sum + Number(row.num_entries || 0), 0);
  const working = queues.adapter_engine.reduce((sum, row) => sum + Number(row.threads_working || 0), 0);
  const maxThread = queues.adapter_engine.reduce((sum, row) => sum + Number(row.max_thread || 0), 0);
  const errors = queues.integration_engine.reduce((sum, row) => sum + Number(row.fail || 0), 0);

  return (
    <article className="surface queue-thread-widget">
      <PanelHeader eyebrow="QUEUE & THREAD" title="운영 엔진 상태" action={errors ? `${errors} errors` : "normal"} />
      {loading && !queues.adapter_engine.length && !queues.integration_engine.length
        ? <p className="widget-loading">Queue와 Thread 상태를 불러오는 중입니다.</p>
        : (
      <div className="engine-metrics">
        <div><small>Queue 대기</small><strong>{entries}</strong></div>
        <div><small>Thread</small><strong>{working}<em> / {maxThread}</em></strong></div>
        <div className={errors ? "attention" : ""}><small>시스템 Queue 오류</small><strong>{errors}</strong></div>
      </div>
        )}
      <div className="legacy-source-note"><span>Legacy 연결</span><b>데이터 원본 설정 필요</b></div>
      <button className="text-button" onClick={() => onNavigate("performance")}>노드·Queue 상세 보기 <span>→</span></button>
    </article>
  );
}

export function LiveInterfacesWidget({ sid, onNavigate }: { sid: string; onNavigate: (view: ViewId) => void }) {
  const [rows, setRows] = useState<MessageRow[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    const load = (initial: boolean) => {
      if (initial) setLoading(true);
      void apiFetch<{ data: MessageRow[] }>(
        `/messages?sid=${encodeURIComponent(sid)}&limit=6&hours=24`,
        { timeoutMs: DASHBOARD_REQUEST_TIMEOUT_MS },
      )
        .then((payload) => {
          if (!cancelled) setRows(payload.data);
        })
        .catch(() => {
          if (!cancelled && initial) setRows([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    };
    const initialTimer = window.setTimeout(() => load(true), 0);
    const refreshTimer = window.setInterval(() => load(false), DASHBOARD_REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(initialTimer);
      window.clearInterval(refreshTimer);
    };
  }, [sid]);
  return (
    <article className="surface live-interface-widget">
      <PanelHeader eyebrow="LIVE INTERFACE" title="실시간 인터페이스 내역" action="15분 자동 갱신" />
      <div className="compact-list">
        {loading && !rows.length && <p className="widget-loading">최근 인터페이스를 불러오는 중입니다.</p>}
        {rows.map((row) => <div key={row.message_id}><span><b>{row.interface_name || "미확인"}</b><small>{row.source_system || "—"} → {row.target_system || "—"}</small></span><i className={`status-pill ${["F", "ERROR", "FAILED"].includes(row.status.toUpperCase()) ? "error" : "running"}`}>{row.status}</i></div>)}
        {!loading && !rows.length && <p className="empty-state">최근 인터페이스 내역이 없습니다.</p>}
      </div>
      <button className="text-button" onClick={() => onNavigate("realtime_interfaces")}>실시간 화면 열기 <span>→</span></button>
    </article>
  );
}

export function DailyCheckWidget({ sid, onNavigate }: { sid: string; onNavigate: (view: ViewId) => void }) {
  const { hrdRows, deliveringRows, loading } = useDailyChecks(sid, DASHBOARD_REFRESH_INTERVAL_MS);
  return (
    <article className="surface daily-check-widget">
      <PanelHeader eyebrow="DAILY CHECK" title="오늘의 운영 점검" action="7일 기준" />
      {loading && !hrdRows.length && !deliveringRows.length
        ? <p className="widget-loading">일일 점검 데이터를 불러오는 중입니다.</p>
        : (
      <div className="daily-widget-grid">
        <div><span>HRD 인터페이스 현행</span><strong>{hrdRows.length}</strong><small>HRD 키워드</small></div>
        <div className={deliveringRows.length ? "attention" : ""}><span>Delivering</span><strong>{deliveringRows.length}</strong><small>최근 7일</small></div>
      </div>
        )}
      <button className="text-button" onClick={() => onNavigate("daily_checks")}>일일 점검 열기 <span>→</span></button>
    </article>
  );
}
