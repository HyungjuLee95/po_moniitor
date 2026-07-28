"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "../../core/api";
import type { MonitoringPolicy, PoServer, User } from "../../core/types";
import { UserManagementPanel } from "../auth/UserManagementPanel";
import { CollectorsPage } from "../collectors/CollectorsPage";


type SapCheck = {
  sid: string;
  live_mode: boolean;
  ready: boolean;
  services: Array<{ service: string; status: string; operations?: string[]; detail?: string }>;
};

type SettingsTab = "connections" | "monitoring" | "users" | "collector";

export function SettingsPage({ sid, server, servers, user }: { sid: string; server?: PoServer; servers: PoServer[]; user: User }) {
  const [tab, setTab] = useState<SettingsTab>("connections");
  const [sap, setSap] = useState<SapCheck | null>(null);
  const [rtims, setRtims] = useState<{ enabled: boolean; ready: boolean } | null>(null);
  const [policy, setPolicy] = useState<MonitoringPolicy | null>(null);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");

  const loadPolicy = useCallback(async () => {
    try {
      const payload = await apiFetch<{ data: MonitoringPolicy }>(`/configuration/monitoring-policy?sid=${encodeURIComponent(sid)}`);
      setPolicy(payload.data);
    } catch {
      setNotice("모니터링 기준을 불러오지 못했습니다.");
    }
  }, [sid]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadPolicy(), 0);
    return () => window.clearTimeout(timer);
  }, [loadPolicy]);

  const check = async () => {
    setLoading(true);
    setNotice("");
    try {
      const [sapPayload, rtimsPayload] = await Promise.all([
        apiFetch<{ data: SapCheck }>(`/configuration/sap-po-check?sid=${encodeURIComponent(sid)}`),
        apiFetch<{ data: { enabled: boolean; ready: boolean } }>("/configuration/rtims-check"),
      ]);
      setSap(sapPayload.data);
      setRtims(rtimsPayload.data);
    } catch {
      setNotice("연결 검사에 실패했습니다. 내부망과 서버 설정을 확인하세요.");
    } finally {
      setLoading(false);
    }
  };

  const savePolicy = async () => {
    if (!policy) return;
    try {
      const payload = await apiFetch<{ data: MonitoringPolicy }>(`/configuration/monitoring-policy?sid=${encodeURIComponent(sid)}`, {
        method: "PUT",
        body: JSON.stringify(policy),
      });
      setPolicy(payload.data);
      setNotice("모니터링 기준을 저장했습니다.");
    } catch {
      setNotice("모니터링 기준 저장에 실패했습니다.");
    }
  };

  return (
    <section className="feature-page settings-page">
      <header className="feature-header">
        <div><p className="kicker">ADMINISTRATION</p><h2>환경 설정</h2><p>연결 상태, 모니터링 기준, 사용자 권한과 수집 상태를 관리합니다.</p></div>
      </header>
      <nav className="settings-tabs" aria-label="환경 설정 메뉴">
        <button className={tab === "connections" ? "active" : ""} onClick={() => setTab("connections")}>연결 상태</button>
        <button className={tab === "monitoring" ? "active" : ""} onClick={() => setTab("monitoring")}>모니터링 기준</button>
        <button className={tab === "users" ? "active" : ""} onClick={() => setTab("users")}>사용자·권한</button>
        <button className={tab === "collector" ? "active" : ""} onClick={() => setTab("collector")}>수집 상태</button>
      </nav>
      {notice && <p className="inline-notice">{notice}</p>}

      {tab === "connections" && (
        <section className="settings-section">
          <header className="settings-section-header"><div><p className="kicker">CONNECTIONS</p><h3>서버 연결 상태</h3><p>민감정보를 노출하지 않고 SAP PO·RTIMS 연결 계약을 검사합니다.</p></div><button className="primary-button" onClick={() => void check()} disabled={loading}>{loading ? "검사 중…" : "연결 검사"}</button></header>
          <div className="settings-grid">
            <article><p className="kicker">ACTIVE SERVER</p><h3>{server?.display_name || sid}</h3><dl><div><dt>SID</dt><dd>{sid}</dd></div><div><dt>환경</dt><dd>{server?.environment || "—"}</dd></div><div><dt>기능</dt><dd>{server?.capabilities.join(", ") || "—"}</dd></div></dl></article>
            <article><p className="kicker">RTIMS ORACLE</p><h3>{rtims === null ? "검사 전" : rtims.ready ? "연결 정상" : rtims.enabled ? "연결 실패" : "비활성"}</h3><p>대시보드, 메시지, 장애와 채널별 통계 원본</p></article>
            <article className="span-two"><p className="kicker">SAP PO SERVICES</p><h3>{sap === null ? "검사 전" : sap.ready ? "모든 서비스 정상" : "일부 서비스 확인 필요"}</h3><div className="service-checks">{sap?.services.map((service) => <div key={service.service}><span>{service.service}</span><i className={`status-pill ${service.status === "ok" ? "running" : "error"}`}>{service.status}</i><small>{service.operations?.length ?? 0} operations</small></div>)}</div></article>
          </div>
        </section>
      )}

      {tab === "monitoring" && policy && (
        <section className="settings-section">
          <header className="settings-section-header"><div><p className="kicker">MONITORING POLICY</p><h3>{sid} 응답시간 기준</h3><p>대시보드 평균과 지연 메시지 목록에 동일하게 적용됩니다.</p></div><button className="primary-button" onClick={() => void savePolicy()}>기준 저장</button></header>
          <div className="policy-form">
            <label><span>평균 조회 범위</span><select value={policy.response_window_minutes} onChange={(event) => setPolicy({ ...policy, response_window_minutes: Number(event.target.value) })}><option value="15">최근 15분</option><option value="30">최근 30분</option><option value="60">최근 1시간</option><option value="360">최근 6시간</option><option value="1440">최근 24시간</option></select></label>
            <label><span>지연 기준</span><div><input type="number" min="0.1" step="0.1" value={policy.slow_threshold_ms / 1000} onChange={(event) => setPolicy({ ...policy, slow_threshold_ms: Math.round(Number(event.target.value) * 1000) })} /><em>초</em></div></label>
            <label><span>심각 지연 기준</span><div><input type="number" min="0.1" step="0.1" value={policy.critical_threshold_ms / 1000} onChange={(event) => setPolicy({ ...policy, critical_threshold_ms: Math.round(Number(event.target.value) * 1000) })} /><em>초</em></div></label>
            <label><span>최대 상세 건수</span><div><input type="number" min="10" max="500" step="10" value={policy.max_detail_rows} onChange={(event) => setPolicy({ ...policy, max_detail_rows: Number(event.target.value) })} /><em>건</em></div></label>
          </div>
        </section>
      )}

      {tab === "users" && <UserManagementPanel servers={servers} currentUsername={user.username} />}
      {tab === "collector" && <CollectorsPage user={user} embedded />}
    </section>
  );
}
