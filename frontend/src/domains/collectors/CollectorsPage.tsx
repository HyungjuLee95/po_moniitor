"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import type { User } from "../../core/types";


type Collector = {
  sid: string;
  server_name: string;
  status: string;
  last_success_at: string | null;
  item_count: number;
};

export function CollectorsPage({ user, embedded = false }: { user: User; embedded?: boolean }) {
  const [rows, setRows] = useState<Collector[]>([]);
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState("");
  const canRun = user.permissions.includes("*") || user.permissions.includes("collectors:run");

  const load = useCallback(async () => {
    try {
      const payload = await apiFetch<{ data: Collector[] }>("/collectors");
      setRows(payload.data);
    } catch {
      setNotice("Collector 상태를 불러오지 못했습니다.");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const run = async (sids: string[]) => {
    setRunning(true);
    setNotice("");
    try {
      const payload = await apiFetch<{ data: Array<{ sid: string; status: string; fetched: number }> }>("/collectors/run", {
        method: "POST",
        body: JSON.stringify({ sids }),
      });
      setNotice(payload.data.map((row) => `${row.sid} ${row.fetched}건`).join(" · "));
      await load();
    } catch {
      setNotice("수동 수집에 실패했습니다. SAP PO 연결과 권한을 확인하세요.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <section className={embedded ? "settings-section" : "feature-page"}>
      <header className="feature-header">
        <div><p className="kicker">COLLECTOR CONTROL</p><h2>Collector 상태</h2><p>서버별 수집 준비 상태와 수동 실행 결과를 확인합니다.</p></div>
        {canRun && <button className="primary-button" onClick={() => void run(rows.map((row) => row.sid))} disabled={running}>{running ? "수집 중…" : "전체 수동 수집"}</button>}
      </header>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="collector-grid">
        {rows.map((row) => (
          <article key={row.sid}>
            <header><span>{row.sid}</span><i className={`status-pill ${row.status.toLowerCase()}`}>{row.status}</i></header>
            <h3>{row.server_name}</h3>
            <dl><div><dt>마지막 성공</dt><dd>{row.last_success_at ? new Date(row.last_success_at).toLocaleString("ko-KR") : "아직 없음"}</dd></div><div><dt>수집 건수</dt><dd>{row.item_count.toLocaleString()}</dd></div></dl>
            {canRun && <button className="secondary-button" onClick={() => void run([row.sid])} disabled={running}>이 서버 수집</button>}
          </article>
        ))}
      </div>
    </section>
  );
}
