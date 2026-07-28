"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import type { User } from "../../core/types";


type Incident = {
  error_log_id?: number;
  incident_key?: string;
  msgguid?: string;
  server_id?: string;
  sid?: string;
  ob_intf_nm?: string;
  interface_name?: string;
  category_nm?: string;
  incident_type?: string;
  error_text?: string;
  detail?: string;
  error_state?: string;
  status?: string;
  first_seen_at?: string;
  last_seen_at?: string;
};

export function IncidentsPage({ sid, user }: { sid: string; user: User }) {
  const [rows, setRows] = useState<Incident[]>([]);
  const [hours, setHours] = useState("24");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const canResolve = user.permissions.includes("*") || user.permissions.includes("incidents:resolve");

  const load = useCallback(async () => {
    setLoading(true);
    setNotice("");
    try {
      const payload = await apiFetch<{ data: Incident[] }>(`/incidents?sid=${encodeURIComponent(sid)}&hours=${hours}&limit=100&offset=0`);
      setRows(payload.data);
    } catch {
      setRows([]);
      setNotice("장애 이력을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [hours, sid]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const resolve = async (row: Incident) => {
    if (!row.error_log_id || !canResolve) return;
    try {
      await apiFetch(`/incidents/${row.error_log_id}/resolve`, {
        method: "PATCH",
        body: JSON.stringify({ message: "PO Monitor에서 확인 완료" }),
      });
      setNotice("장애를 해결 상태로 변경했습니다.");
      await load();
    } catch {
      setNotice("해결 처리에 실패했습니다. RTIMS 연결과 권한을 확인하세요.");
    }
  };

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div><p className="kicker">INCIDENT HISTORY</p><h2>장애 관리</h2><p>{sid}의 오류 이력과 처리 상태를 관리합니다.</p></div>
        <label className="compact-select"><span>조회 기간</span><select value={hours} onChange={(event) => setHours(event.target.value)}><option value="24">24시간</option><option value="72">3일</option><option value="168">7일</option></select></label>
      </header>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="incident-list">
        {rows.map((row, index) => {
          const state = row.error_state || row.status || "OPEN";
          return (
            <article key={row.error_log_id ?? row.incident_key ?? index}>
              <header><span className={`severity ${state === "C" ? "info" : "critical"}`}>{state === "C" ? "resolved" : row.incident_type || row.category_nm || "error"}</span><small>{row.last_seen_at ? new Date(row.last_seen_at).toLocaleString("ko-KR") : sid}</small></header>
              <h3>{row.ob_intf_nm || row.interface_name || row.msgguid || "확인되지 않은 인터페이스"}</h3>
              <p>{row.error_text || row.detail || "상세 오류 내용이 없습니다."}</p>
              <footer><span>{row.server_id || row.sid || sid}</span><span>{row.first_seen_at ? `최초 ${new Date(row.first_seen_at).toLocaleString("ko-KR")}` : "최근 감지"}</span>{canResolve && row.error_log_id && state !== "C" && <button onClick={() => void resolve(row)}>해결 처리</button>}</footer>
            </article>
          );
        })}
        {!loading && !rows.length && <p className="empty-state">조회 기간에 발생한 장애가 없습니다.</p>}
      </div>
    </section>
  );
}
