"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";


type Performance = {
  interface_name: string;
  source_system: string;
  target_system: string;
  total_count: number;
  success_count: number;
  fail_count: number;
  pending_count: number;
  success_rate: number;
  avg_latency_ms: number;
  max_latency_ms: number;
};

type Resource = {
  resource_id: number;
  resource_type: string;
  resource_name: string;
  node: string;
  recent_usage: number;
  max_usage: number;
  max_limit: number;
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

export function PerformancePage({ sid }: { sid: string }) {
  const [hours, setHours] = useState("24");
  const [performance, setPerformance] = useState<Performance[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [queues, setQueues] = useState<QueueData>({ adapter_engine: [], integration_engine: [] });
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setNotice("");
      Promise.all([
        apiFetch<{ data: Performance[] }>(`/monitoring/performance?sid=${encodeURIComponent(sid)}&hours=${hours}`),
        apiFetch<{ data: Resource[] }>(`/monitoring/resources?sid=${encodeURIComponent(sid)}`),
        apiFetch<{ data: QueueData }>(`/monitoring/queues?sid=${encodeURIComponent(sid)}`),
      ])
        .then(([performancePayload, resourcePayload, queuePayload]) => {
          setPerformance(performancePayload.data);
          setResources(resourcePayload.data);
          setQueues(queuePayload.data);
        })
        .catch(() => setNotice("성능·리소스 일부 데이터를 불러오지 못했습니다."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [hours, sid]);
  const resourcesByNode = useMemo(() => {
    const grouped = new Map<string, Resource[]>();
    resources.forEach((resource) => {
      const rows = grouped.get(resource.node) ?? [];
      rows.push(resource);
      grouped.set(resource.node, rows);
    });
    return [...grouped.entries()];
  }, [resources]);

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div><p className="kicker">PERFORMANCE & CAPACITY</p><h2>성능·리소스·Queue</h2><p>{sid}의 인터페이스 처리 성능과 최신 자원·대기열 상태를 확인합니다.</p></div>
        <label className="compact-select"><span>집계 기간</span><select value={hours} onChange={(event) => setHours(event.target.value)}><option value="6">6시간</option><option value="24">24시간</option><option value="72">3일</option><option value="168">7일</option></select></label>
      </header>
      {notice && <p className="inline-notice">{notice}</p>}
      <section className="node-resource-board">
        <div className="table-caption"><b>노드별 CPU·Memory 통합 사용률</b><span>{resourcesByNode.length} nodes</span></div>
        <div className="node-resource-grid">
          {resourcesByNode.map(([node, nodeResources]) => (
            <article key={node}>
              <header><b>{node}</b><span>{nodeResources.length} resources</span></header>
              {nodeResources.map((resource) => {
                const limit = Number(resource.max_limit) || 100;
                const usage = Number(resource.recent_usage) || 0;
                const maximum = Number(resource.max_usage) || 0;
                return (
                  <div className="node-resource-row" key={`${resource.resource_id}-${resource.node}`}>
                    <div><span>{resource.resource_type}</span><b>{resource.resource_name}</b></div>
                    <div className="resource-combined-track">
                      <i className="resource-max" style={{ width: `${Math.min(100, maximum / limit * 100)}%` }} />
                      <i className="resource-current" style={{ width: `${Math.min(100, usage / limit * 100)}%` }} />
                    </div>
                    <strong>{usage.toFixed(1)}<small>% · MAX {maximum.toFixed(1)}</small></strong>
                  </div>
                );
              })}
            </article>
          ))}
          {!resourcesByNode.length && <p className="empty-state">표시할 노드 리소스가 없습니다.</p>}
        </div>
      </section>
      <div className="feature-split">
        <div className="table-card">
          <div className="table-caption"><b>인터페이스 성능</b><span>{performance.length} interfaces</span></div>
          <div className="data-table performance-table">
            <div className="data-row data-head"><span>인터페이스</span><span>처리량</span><span>성공률</span><span>평균</span><span>최대</span></div>
            {performance.map((row) => <div className="data-row" key={`${row.interface_name}-${row.source_system}-${row.target_system}`}><span><b>{row.interface_name}</b><small>{row.source_system} → {row.target_system}</small></span><span>{row.total_count.toLocaleString()}</span><span>{row.success_rate.toFixed(2)}%</span><span>{(row.avg_latency_ms / 1000).toFixed(3)}초</span><span>{(row.max_latency_ms / 1000).toFixed(3)}초</span></div>)}
          </div>
        </div>
        <aside className="detail-card">
          <p className="kicker">QUEUE STATUS</p><h3>대기열 상태</h3>
          <h4>Adapter Engine</h4>
          <div className="compact-list">{queues.adapter_engine.map((queue) => <div key={`${queue.servernode}-${queue.queuename}`}><span><b>{queue.queuename}</b><small>{queue.servernode} · Thread {queue.threads_working}/{queue.max_thread}</small></span><i className={`status-pill ${queue.started === "Y" ? "running" : "stopped"}`}>{queue.num_entries}</i></div>)}</div>
          <h4>Integration Engine</h4>
          <div className="compact-list">{queues.integration_engine.map((queue) => <div key={`${queue.client_id}-${queue.direction}`}><span><b>Client {queue.client_id}</b><small>{queue.direction} · 정상 {queue.normal}</small></span><i className={`status-pill ${queue.fail ? "error" : "running"}`}>{queue.warning + queue.fail}</i></div>)}</div>
        </aside>
      </div>
    </section>
  );
}
