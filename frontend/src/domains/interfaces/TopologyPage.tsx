"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";


type Edge = {
  source_system: string;
  target_system: string;
  interface_name: string;
  source_namespace: string;
  target_namespace: string;
};

export function TopologyPage({ sid }: { sid: string }) {
  const [edges, setEdges] = useState<Edge[]>([]);
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    apiFetch<{ data: Edge[] }>(`/interfaces/topology?sid=${encodeURIComponent(sid)}`)
      .then((payload) => setEdges(payload.data))
      .catch(() => setNotice("시스템 연결 관계를 불러오지 못했습니다."));
  }, [sid]);

  const groups = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const filtered = normalized
      ? edges.filter((edge) => Object.values(edge).some((value) => value.toLowerCase().includes(normalized)))
      : edges;
    const result = new Map<string, Edge[]>();
    filtered.forEach((edge) => {
      const key = `${edge.source_system}→${edge.target_system}`;
      result.set(key, [...(result.get(key) || []), edge]);
    });
    return [...result.entries()];
  }, [edges, query]);

  return (
    <section className="feature-page">
      <header className="feature-header"><div><p className="kicker">SYSTEM TOPOLOGY</p><h2>시스템 연결 관계</h2><p>{sid}의 송신·수신 시스템과 인터페이스 경로를 표시합니다.</p></div></header>
      <div className="feature-toolbar"><label className="search-field"><span>연결 검색</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="시스템, 인터페이스, Namespace" /></label></div>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="topology-grid">
        {groups.map(([key, group]) => (
          <article key={key}>
            <header><span><b>{group[0].source_system}</b><small>SOURCE</small></span><i>→</i><span><b>{group[0].target_system}</b><small>TARGET</small></span></header>
            <div>{group.map((edge) => <p key={`${edge.interface_name}-${edge.source_namespace}`}><b>{edge.interface_name}</b><small>{edge.source_namespace} → {edge.target_namespace}</small></p>)}</div>
          </article>
        ))}
        {!groups.length && <p className="empty-state">표시할 연결 관계가 없습니다.</p>}
      </div>
    </section>
  );
}
