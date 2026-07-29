"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import type { BusinessSystem, ChannelInventoryRow } from "../../core/types";


export function InterfacesPage({ sid }: { sid: string }) {
  const [systems, setSystems] = useState<BusinessSystem[]>([]);
  const [selectedSystem, setSelectedSystem] = useState("");
  const [channels, setChannels] = useState<ChannelInventoryRow[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [detail, setDetail] = useState<{ channel_id: string; component_id: string; attributes: Record<string, unknown> } | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      setSelectedSystem("");
      setChannels([]);
      setDetail(null);
      apiFetch<{ data: BusinessSystem[] }>(`/interfaces?sid=${encodeURIComponent(sid)}`)
        .then((payload) => setSystems(payload.data))
        .catch(() => setNotice("등록 시스템을 불러오지 못했습니다."))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [sid]);

  const openSystem = async (systemId: string) => {
    setSelectedSystem(systemId);
    setLoading(true);
    setNotice("");
    try {
      const payload = await apiFetch<{ data: ChannelInventoryRow[] }>(`/channels/inventory?sid=${encodeURIComponent(sid)}&component_id=${encodeURIComponent(systemId)}&channel_pattern=*`);
      setChannels(payload.data);
    } catch {
      setChannels([]);
      setNotice("선택한 시스템의 채널을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const openChannel = async (channel: ChannelInventoryRow) => {
    setNotice("");
    try {
      const payload = await apiFetch<{ data: { channel_id: string; component_id: string; attributes: Record<string, unknown> } }>(
        `/channels/detail?sid=${encodeURIComponent(sid)}&component_id=${encodeURIComponent(channel.component_id)}&channel_id=${encodeURIComponent(channel.channel_id)}`,
      );
      setDetail(payload.data);
    } catch {
      setDetail(null);
      setNotice("선택한 채널의 상세 정보를 불러오지 못했습니다.");
    }
  };

  const filteredSystems = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return systems;
    return systems.filter((system) => (
      system.name.toLowerCase().includes(normalized)
      || system.business_system_id.toLowerCase().includes(normalized)
    ));
  }, [query, systems]);

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div>
          <p className="kicker">SYSTEM DIRECTORY</p>
          <h2>서버별 등록 시스템과 채널</h2>
          <p>{sid}의 BusinessSystemIn 목록에서 시스템을 선택하면 포함 채널을 조회합니다.</p>
        </div>
      </header>
      <div className="feature-toolbar">
        <label className="search-field"><span>시스템 검색</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="시스템 ID 또는 이름" /></label>
        <label className="compact-select"><span>비즈니스 시스템</span><select value={selectedSystem} onChange={(event) => void openSystem(event.target.value)}><option value="">시스템 선택</option>{filteredSystems.map((system) => <option value={system.business_system_id} key={system.business_system_id}>{system.name} · {system.business_system_id}</option>)}</select></label>
      </div>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="feature-split system-channel-browser">
        <div className="table-card">
          <div className="table-caption"><b>{selectedSystem || "시스템을 선택하세요"}</b><span>{channels.length} channels</span></div>
          <div className="data-table system-channel-table">
            <div className="data-row data-head"><span>채널</span><span>Party</span><span>SID</span><span /></div>
            {channels.map((channel) => (
              <div className="data-row" key={`${channel.component_id}-${channel.channel_id}`}>
                <span><b>{channel.channel_id}</b><small>{channel.component_id}</small></span>
                <span>{channel.party_id || "—"}</span>
                <span>{channel.sid}</span>
                <span><button className="row-action" onClick={() => void openChannel(channel)}>상세</button></span>
              </div>
            ))}
            {!channels.length && <p className="empty-state">{loading ? "조회 중입니다." : "시스템을 선택하면 포함 채널이 표시됩니다."}</p>}
          </div>
        </div>
        <aside className="detail-card">
          {detail ? <><p className="kicker">CHANNEL DETAIL</p><h3>{detail.channel_id}</h3><p className="detail-subtitle">{detail.component_id}</p><dl className="attribute-list">{Object.entries(detail.attributes).slice(0, 24).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{String(value ?? "")}</dd></div>)}</dl></> : <div className="detail-empty"><span>⌁</span><b>채널 상세 대기</b><p>비즈니스 시스템을 선택한 뒤 채널 상세 버튼을 누르세요.</p></div>}
        </aside>
      </div>
    </section>
  );
}
