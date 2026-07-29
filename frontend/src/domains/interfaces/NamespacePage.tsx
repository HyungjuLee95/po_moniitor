"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";


type NamespaceRow = {
  interface_name: string;
  namespace: string;
  direction: string;
  source_system?: string | null;
  target_system?: string | null;
  operation?: string | null;
};


export function NamespacePage({ sid }: { sid: string }) {
  const [rows, setRows] = useState<NamespaceRow[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<{ data: NamespaceRow[] }>(`/interfaces/namespaces?sid=${encodeURIComponent(sid)}`)
      .then((payload) => { setRows(payload.data); setError(""); })
      .catch(() => { setRows([]); setError("Namespace 인벤토리를 불러오지 못했습니다."); });
  }, [sid]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((row) => Object.values(row).some((value) => String(value ?? "").toLowerCase().includes(needle)));
  }, [query, rows]);

  return (
    <section className="feature-page">
      <header className="feature-header"><div><p className="kicker">INTERFACE MONITOR</p><h2>Namespace 인벤토리</h2><p>SAP InterfaceMonitor에서 인터페이스와 Namespace를 조회합니다.</p></div></header>
      <div className="feature-toolbar"><label className="search-field"><span>검색</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="인터페이스, Namespace, 시스템" /></label></div>
      {error && <p className="inline-notice">{error}</p>}
      <div className="table-card"><div className="table-caption"><b>{filtered.length} namespaces</b><span>{sid}</span></div>
        <div className="data-table namespace-table">
          <div className="data-row data-head"><span>인터페이스</span><span>Namespace</span><span>방향</span><span>송신</span><span>수신</span><span>Operation</span></div>
          {filtered.map((row, index) => <div className="data-row" key={`${row.interface_name}|${row.namespace}|${index}`}><span><b>{row.interface_name || "—"}</b></span><span>{row.namespace || "—"}</span><span>{row.direction || "—"}</span><span>{row.source_system || "—"}</span><span>{row.target_system || "—"}</span><span>{row.operation || "—"}</span></div>)}
          {!filtered.length && <p className="empty-state">표시할 Namespace가 없습니다.</p>}
        </div>
      </div>
    </section>
  );
}
