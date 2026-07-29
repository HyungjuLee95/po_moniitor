"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import { DASHBOARD_REFRESH_INTERVAL_MS, DASHBOARD_REQUEST_TIMEOUT_MS } from "../../core/refresh";
import type { MonitoringSummary, PoServer } from "../../core/types";
import { PanelHeader } from "../dashboard/PanelHeader";

type ThroughputBucket = {
  bucket: string;
  label: string;
  hour: number | null;
  total_count: number;
  success_count: number;
  fail_count: number;
  pending_count: number;
  total_size_bytes: number;
};

type TrafficGranularity = "hour" | "day";

export function formatLatencySeconds(milliseconds: number): string {
  return `${(milliseconds / 1000).toFixed(3)}초`;
}

export function HealthMetrics({
  summary,
  loading,
  expanded,
  onToggle,
}: {
  summary: MonitoringSummary;
  loading: boolean;
  expanded: "issues" | "latency" | null;
  onToggle: (value: "issues" | "latency") => void;
}) {
  if (loading) {
    return (
      <section className="metric-grid" aria-label="운영 지표를 불러오는 중">
        {Array.from({ length: 4 }, (_, index) => (
          <article className="metric-card dashboard-skeleton" key={index}>
            <span />
            <strong />
            <small />
          </article>
        ))}
      </section>
    );
  }
  return (
    <section className="metric-grid">
      <Metric label="총 메시지량" value={summary.messages_today.toLocaleString()} meta="오늘 누적 처리" accent="blue" trend="TODAY" />
      <Metric label="성공률" value={`${Number(summary.success_rate ?? 0).toFixed(2)}%`} meta="성공 메시지 비율" accent="green" trend="SUCCESS" />
      <Metric label="실패 건수" value={Number(summary.failed_messages ?? 0).toLocaleString()} meta={`Delivering ${Number(summary.pending_messages ?? 0).toLocaleString()}건`} accent="red" trend={expanded === "issues" ? "접기" : "상세 보기"} onClick={() => onToggle("issues")} expanded={expanded === "issues"} />
      <Metric label="평균 응답" value={formatLatencySeconds(summary.average_latency_ms)} meta={`최근 ${summary.latency_window_minutes}분 기준`} accent="violet" trend={expanded === "latency" ? "접기" : "지연 목록"} onClick={() => onToggle("latency")} expanded={expanded === "latency"} />
    </section>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes.toLocaleString()} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

function dateKey(value: Date): string {
  return [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, "0"),
    String(value.getDate()).padStart(2, "0"),
  ].join("");
}

function emptyBuckets(granularity: TrafficGranularity): ThroughputBucket[] {
  const now = new Date();
  if (granularity === "hour") {
    const prefix = dateKey(now);
    return Array.from({ length: 24 }, (_, hour) => ({
      bucket: `${prefix}${String(hour).padStart(2, "0")}`,
      label: `${String(hour).padStart(2, "0")}:00`,
      hour,
      total_count: 0,
      success_count: 0,
      fail_count: 0,
      pending_count: 0,
      total_size_bytes: 0,
    }));
  }
  return Array.from({ length: 7 }, (_, index) => {
    const day = new Date(now);
    day.setDate(now.getDate() - (6 - index));
    return {
      bucket: dateKey(day),
      label: `${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`,
      hour: null,
      total_count: 0,
      success_count: 0,
      fail_count: 0,
      pending_count: 0,
      total_size_bytes: 0,
    };
  });
}

function mergeTrafficRows(
  payloads: ThroughputBucket[][],
  granularity: TrafficGranularity,
): ThroughputBucket[] {
  const merged = new Map(
    emptyBuckets(granularity).map((row) => [row.bucket, row]),
  );
  payloads.flat().forEach((row) => {
    const current = merged.get(row.bucket) ?? {
      ...row,
      total_count: 0,
      success_count: 0,
      fail_count: 0,
      pending_count: 0,
      total_size_bytes: 0,
    };
    merged.set(row.bucket, {
      ...current,
      label: row.label,
      hour: row.hour,
      total_count: current.total_count + row.total_count,
      success_count: current.success_count + row.success_count,
      fail_count: current.fail_count + row.fail_count,
      pending_count: current.pending_count + row.pending_count,
      total_size_bytes: current.total_size_bytes + row.total_size_bytes,
    });
  });
  return [...merged.values()].sort((left, right) => left.bucket.localeCompare(right.bucket));
}

export function ThroughputWidget({
  sid,
  servers,
}: {
  sid: string;
  servers: PoServer[];
}) {
  const [rows, setRows] = useState<ThroughputBucket[]>([]);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState("ALL");
  const [granularity, setGranularity] = useState<TrafficGranularity>("hour");
  const trafficServers = useMemo(() => {
    const monitorServers = servers.filter(
      (server) => server.enabled && server.capabilities.includes("monitor"),
    );
    const popPmp = monitorServers.filter((server) => ["POP", "PMP"].includes(server.sid.toUpperCase()));
    return popPmp.length ? popPmp : monitorServers;
  }, [servers]);

  useEffect(() => {
    const selectedServers = scope === "ALL"
      ? trafficServers
      : trafficServers.filter((server) => server.sid === scope);
    const fallbackServer = servers.find((server) => server.sid === sid);
    const targets = selectedServers.length
      ? selectedServers
      : fallbackServer ? [fallbackServer] : [];

    let cancelled = false;
    const days = granularity === "hour" ? 1 : 7;
    const load = (initial: boolean) => {
      if (initial) setLoading(true);
      void Promise.allSettled(
        targets.map((server) => apiFetch<{ data: ThroughputBucket[] }>(
          `/monitoring/throughput?sid=${encodeURIComponent(server.sid)}&granularity=${granularity}&days=${days}`,
          { timeoutMs: DASHBOARD_REQUEST_TIMEOUT_MS },
        )),
      ).then((results) => {
        if (cancelled) return;
        const successful = results
          .filter((result): result is PromiseFulfilledResult<{ data: ThroughputBucket[] }> => result.status === "fulfilled")
          .map((result) => result.value.data);
        setRows(mergeTrafficRows(successful, granularity));
        const failedCount = results.length - successful.length;
        setNotice(
          targets.length === 0
            ? "조회 가능한 모니터링 서버가 없습니다."
            : failedCount
              ? `${targets.length}개 서버 중 ${failedCount}개 서버 데이터를 불러오지 못해 나머지만 합산했습니다.`
              : "",
        );
      }).finally(() => {
        if (!cancelled) setLoading(false);
      });
    };
    const initialTimer = window.setTimeout(() => load(true), 0);
    const refreshTimer = window.setInterval(
      () => load(false),
      DASHBOARD_REFRESH_INTERVAL_MS,
    );
    return () => {
      cancelled = true;
      window.clearTimeout(initialTimer);
      window.clearInterval(refreshTimer);
    };
  }, [granularity, scope, servers, sid, trafficServers]);

  const max = useMemo(
    () => Math.max(1, ...rows.map((row) => row.total_count)),
    [rows],
  );
  const scopeLabel = scope === "ALL"
    ? `전체 (${trafficServers.map((server) => server.sid).join(" + ") || sid})`
    : scope;
  const axisLabels = granularity === "hour"
    ? ["00:00", "06:00", "12:00", "18:00", "24:00"]
    : rows
      .filter((_, index) => index === 0 || index === Math.floor(rows.length / 2) || index === rows.length - 1)
      .map((row) => row.label);

  return (
    <article className="surface throughput-card span-two">
      <PanelHeader eyebrow="MESSAGE THROUGHPUT" title="메시지 트래픽" action={`${scopeLabel} · ${granularity === "hour" ? "1시간" : "1일"}`} />
      <div className="traffic-toolbar" aria-label="메시지 트래픽 조회 조건">
        <label>
          <span>서버</span>
          <select value={scope} onChange={(event) => setScope(event.target.value)}>
            <option value="ALL">전체 ({trafficServers.map((server) => server.sid).join(" + ") || sid})</option>
            {trafficServers.map((server) => (
              <option key={server.sid} value={server.sid}>{server.display_name} ({server.sid})</option>
            ))}
          </select>
        </label>
        <div className="traffic-granularity" aria-label="집계 단위">
          <button type="button" className={granularity === "hour" ? "active" : ""} onClick={() => setGranularity("hour")}>1시간</button>
          <button type="button" className={granularity === "day" ? "active" : ""} onClick={() => setGranularity("day")}>1일</button>
        </div>
        <small>{granularity === "hour" ? "오늘 00:00:00 ~ 23:59:59" : "최근 7일 · 일별 합계"}</small>
      </div>
      <div className="throughput-chart">
        <div className="chart-scale"><span>{Math.round(max / 1000)}K</span><span>{Math.round(max * .67 / 1000)}K</span><span>{Math.round(max * .33 / 1000)}K</span><span>0</span></div>
        <div className="chart-bars">
          {rows.map((row) => (
            <button
              type="button"
              className="traffic-bar"
              key={row.bucket}
              style={{ height: `${Math.max(3, row.total_count / max * 100)}%` }}
              aria-label={`${row.label}, 메시지 ${row.total_count.toLocaleString()}건, 총 크기 ${formatBytes(row.total_size_bytes)}`}
            >
              <span className="traffic-tooltip">
                <b>{row.label}</b>
                <span>메시지 <strong>{row.total_count.toLocaleString()}건</strong></span>
                <span>총 크기 <strong>{formatBytes(row.total_size_bytes)}</strong></span>
              </span>
            </button>
          ))}
        </div>
      </div>
      <div className="chart-axis">{axisLabels.map((label) => <span key={label}>{label}</span>)}</div>
      {loading && !rows.length && <p className="chart-notice">트래픽 데이터를 불러오는 중입니다.</p>}
      {notice && <p className="chart-notice">{notice}</p>}
    </article>
  );
}

function Metric({ label, value, meta, accent, trend, onClick, expanded }: { label: string; value: string; meta: string; accent: string; trend: string; onClick?: () => void; expanded?: boolean }) {
  const content = (
    <>
      <div><span>{label}</span><i /></div>
      <strong>{value}</strong>
      <footer><small>{meta}</small><em>{trend}</em></footer>
    </>
  );
  if (onClick) {
    return <button className={`metric-card metric-action ${accent}`} onClick={onClick} aria-expanded={expanded}>{content}</button>;
  }
  return <article className={`metric-card ${accent}`}>{content}</article>;
}
