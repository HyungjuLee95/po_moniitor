"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "../../core/api";


type SystemStat = {
  group_id: number | null;
  system_name: string | null;
  success_count: number;
  fail_count: number;
  pending_count: number;
  closed_count: number;
  total_count: number;
  success_rate: number;
};
type QueueStatus = { server_id: string; client_id: string; normal: number; warning: number; fail: number };


export function SystemStatusPage({ sid }: { sid: string }) {
  const [stats, setStats] = useState<SystemStat[]>([]);
  const [queues, setQueues] = useState<QueueStatus[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      apiFetch<{ data: SystemStat[] }>(`/monitoring/system-statistics?sid=${encodeURIComponent(sid)}&hours=24`),
      apiFetch<{ data: QueueStatus[] }>(`/monitoring/system-queue-status?sid=${encodeURIComponent(sid)}`),
    ]).then(([statPayload, queuePayload]) => {
      setStats(statPayload.data);
      setQueues(queuePayload.data);
      setError("");
    }).catch(() => {
      setStats([]);
      setQueues([]);
      setError("시스템 통계와 대기 현황을 불러오지 못했습니다.");
    });
  }, [sid]);

  return (
    <section className="feature-page">
      <header className="feature-header"><div><p className="kicker">SYSTEM FLOW</p><h2>시스템 그룹별 통계·대기 상세</h2><p>최근 24시간 처리량과 클라이언트별 정상·경고·실패 대기 건수를 함께 봅니다.</p></div></header>
      {error && <p className="inline-notice">{error}</p>}
      <div className="feature-split">
        <div className="table-card"><div className="table-caption"><b>시스템 그룹</b><span>{stats.length} groups</span></div>
          <div className="data-table system-stat-table"><div className="data-row data-head"><span>그룹</span><span>전체</span><span>성공</span><span>실패</span><span>대기</span><span>성공률</span></div>
            {stats.map((row, index) => <div className="data-row" key={`${row.group_id}|${index}`}><span><b>{row.system_name || "미분류"}</b></span><span>{row.total_count.toLocaleString()}</span><span>{row.success_count.toLocaleString()}</span><span>{row.fail_count.toLocaleString()}</span><span>{row.pending_count.toLocaleString()}</span><span>{row.success_rate.toFixed(2)}%</span></div>)}
          </div>
        </div>
        <div className="table-card"><div className="table-caption"><b>Queue 대기</b><span>{queues.length} clients</span></div>
          <div className="data-table queue-detail-table"><div className="data-row data-head"><span>Client</span><span>정상</span><span>경고</span><span>실패</span></div>
            {queues.map((row) => <div className="data-row" key={`${row.server_id}|${row.client_id}`}><span><b>{row.client_id}</b><small>{row.server_id}</small></span><span>{row.normal}</span><span>{row.warning}</span><span>{row.fail}</span></div>)}
          </div>
        </div>
      </div>
    </section>
  );
}
