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

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true);
      setSelectedSystem("");
      setChannels([]);
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
      </div>
      {notice && <p className="inline-notice">{notice}</p>}
      <div className="system-browser">
        <div className="system-list">
          <div className="table-caption"><b>등록 시스템</b><span>{filteredSystems.length} systems</span></div>
          {filteredSystems.map((system) => (
            <button className={selectedSystem === system.business_system_id ? "active" : ""} key={system.business_system_id} onClick={() => void openSystem(system.business_system_id)}>
              <span><b>{system.name}</b><small>{system.business_system_id}</small></span><em>›</em>
            </button>
          ))}
          {!loading && !filteredSystems.length && <p className="empty-state">등록 시스템이 없습니다.</p>}
        </div>
        <div className="table-card">
          <div className="table-caption"><b>{selectedSystem || "시스템을 선택하세요"}</b><span>{channels.length} channels</span></div>
          <div className="data-table system-channel-table">
            <div className="data-row data-head"><span>채널</span><span>Party</span><span>SID</span></div>
            {channels.map((channel) => (
              <div className="data-row" key={`${channel.component_id}-${channel.channel_id}`}>
                <span><b>{channel.channel_id}</b><small>{channel.component_id}</small></span>
                <span>{channel.party_id || "—"}</span>
                <span>{channel.sid}</span>
              </div>
            ))}
            {!channels.length && <p className="empty-state">{loading ? "조회 중입니다." : "시스템을 선택하면 포함 채널이 표시됩니다."}</p>}
          </div>
        </div>
      </div>
    </section>
  );
}
