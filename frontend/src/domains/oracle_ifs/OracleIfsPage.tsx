"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import type { User } from "../../core/types";


type IfsRow = {
  req_seq: string;
  eai_dev_user_id: string | null;
  ifs_ids: string[];
  source_system: string | null;
  target_system: string | null;
  progress_status: string | null;
  process_date: string | null;
  target_date: string | null;
  synced_at: string;
};


export function OracleIfsPage({ user }: { user: User }) {
  const [rows, setRows] = useState<IfsRow[]>([]);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const canSync = user.permissions.includes("*") || user.permissions.includes("oracle-ifs:sync");
  const canWrite = user.permissions.includes("*") || user.permissions.includes("oracle-ifs:write");

  const load = useCallback(async () => {
    try {
      const payload = await apiFetch<{ data: IfsRow[] }>("/oracle-ifs/interfaces");
      setRows(payload.data);
    } catch {
      setRows([]);
      setNotice("Oracle IFS cache를 불러오지 못했습니다.");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const sync = async () => {
    setLoading(true);
    try {
      const payload = await apiFetch<{ data: { status: string; row_count: number } }>("/oracle-ifs/sync", { method: "POST" });
      setNotice(`동기화 ${payload.data.status} · ${payload.data.row_count}건`);
      await load();
    } catch {
      setNotice("Oracle IFS 동기화에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const updateDate = async (reqSeq: string, value: string) => {
    try {
      await apiFetch(`/oracle-ifs/target-date/${encodeURIComponent(reqSeq)}`, {
        method: "PUT",
        body: JSON.stringify({ target_date: value || null }),
      });
      await load();
    } catch {
      setNotice("이관 예정일 변경에 실패했습니다.");
    }
  };

  return (
    <section className="feature-page">
      <header className="feature-header"><div><p className="kicker">ORACLE IFS</p><h2>IFS 동기화 현황</h2><p>사용자별 IFS 요청과 이관 일정을 확인합니다.</p></div>{canSync && <button className="primary-button" onClick={() => void sync()} disabled={loading}>{loading ? "동기화 중…" : "수동 동기화"}</button>}</header>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="table-card"><div className="table-caption"><b>{rows.length} requests</b><span>PostgreSQL cache</span></div>
        <div className="data-table ifs-table"><div className="data-row data-head"><span>요청</span><span>IFS ID</span><span>경로</span><span>상태</span><span>처리일</span><span>이관 예정일</span></div>
          {rows.map((row) => <div className="data-row" key={row.req_seq}><span><b>{row.req_seq}</b><small>{row.eai_dev_user_id || "—"}</small></span><span>{row.ifs_ids.join(", ")}</span><span>{row.source_system || "—"} → {row.target_system || "—"}</span><span>{row.progress_status || "—"}</span><span>{row.process_date || "—"}</span><span>{canWrite ? <input type="date" value={row.target_date || ""} onChange={(event) => void updateDate(row.req_seq, event.target.value)} /> : row.target_date || "—"}</span></div>)}
          {!rows.length && <p className="empty-state">동기화된 IFS 요청이 없습니다.</p>}
        </div>
      </div>
    </section>
  );
}
