"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch } from "../../core/api";
import type {
  ChannelInventoryRow,
  ChannelMessage,
  ChannelRow,
  ChannelStatistics,
  PoServer,
  User,
} from "../../core/types";


type Detail = {
  component_id: string;
  channel_id: string;
  attributes: Record<string, unknown>;
  source: string;
};

const emptyStats: ChannelStatistics = {
  total_count: 0,
  success_count: 0,
  fail_count: 0,
  pending_count: 0,
  avg_elapsed_sec: 0,
  total_msg_size: 0,
  avg_msg_size: 0,
};

function keyOf(row: ChannelInventoryRow): string {
  return `${row.component_id}|${row.channel_id}`;
}

export function ChannelsPage({
  sid,
  server,
  user,
  controlMode = false,
}: {
  sid: string;
  server?: PoServer;
  user: User;
  controlMode?: boolean;
}) {
  const [rows, setRows] = useState<ChannelInventoryRow[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [statistics, setStatistics] = useState<ChannelStatistics>(emptyStats);
  const [history, setHistory] = useState<ChannelMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [notice, setNotice] = useState("");

  const canControl = (
    (user.permissions.includes("*") || user.permissions.includes("channels:control"))
    && Boolean(server?.capabilities.includes("channel-control"))
  );

  const load = useCallback(async () => {
    setLoading(true);
    setNotice("");
    try {
      const [inventoryPayload, statusPayload] = await Promise.all([
        apiFetch<{ data: ChannelInventoryRow[] }>(`/channels/inventory?sid=${encodeURIComponent(sid)}&component_id=*&channel_pattern=*`),
        apiFetch<{ data: ChannelRow[] }>(`/channels?sid=${encodeURIComponent(sid)}`),
      ]);
      const statusMap = new Map(
        statusPayload.data.map((row) => [`${row.component_id}|${row.channel_id}`, row]),
      );
      setRows(inventoryPayload.data.map((row) => ({ ...row, ...statusMap.get(keyOf(row)) })));
      setSelected([]);
    } catch {
      setRows([]);
      setNotice("채널 목록을 불러오지 못했습니다. SAP PO 연결 상태를 확인하세요.");
    } finally {
      setLoading(false);
    }
  }, [sid]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return rows;
    return rows.filter((row) => (
      row.channel_id.toLowerCase().includes(normalized)
      || row.component_id.toLowerCase().includes(normalized)
      || String(row.status ?? "").toLowerCase().includes(normalized)
    ));
  }, [query, rows]);

  const openChannel = async (row: ChannelInventoryRow) => {
    setNotice("");
    try {
      const params = `sid=${encodeURIComponent(sid)}&channel_id=${encodeURIComponent(row.channel_id)}`;
      const [detailPayload, statsPayload, historyPayload] = await Promise.all([
        apiFetch<{ data: Detail }>(`/channels/detail?sid=${encodeURIComponent(sid)}&component_id=${encodeURIComponent(row.component_id)}&channel_id=${encodeURIComponent(row.channel_id)}`),
        apiFetch<{ data: ChannelStatistics }>(`/channels/statistics?${params}`),
        apiFetch<{ data: ChannelMessage[] }>(`/channels/message-history?${params}&limit=10&offset=0`),
      ]);
      setDetail(detailPayload.data);
      setStatistics(statsPayload.data);
      setHistory(historyPayload.data);
    } catch {
      setNotice("채널 상세 또는 RTIMS 통계를 불러오지 못했습니다.");
    }
  };

  const control = async (action: string) => {
    if (!selected.length || !canControl) return;
    setWorking(true);
    setNotice("");
    const targets = rows
      .filter((row) => selected.includes(keyOf(row)))
      .map((row) => ({ component_id: row.component_id, channel_id: row.channel_id }));
    try {
      const payload = await apiFetch<{ data: { succeeded: number; failed: number } }>("/channels/control", {
        method: "POST",
        body: JSON.stringify({ sid, action, channels: targets }),
      });
      setNotice(`${action} 완료 · 성공 ${payload.data.succeeded} / 실패 ${payload.data.failed}`);
      await load();
    } catch {
      setNotice(`${action} 요청에 실패했습니다. 권한과 제어 허용 SID를 확인하세요.`);
    } finally {
      setWorking(false);
    }
  };

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div>
          <p className="kicker">{controlMode ? "CHANNEL CONTROL" : "CHANNEL OBSERVABILITY"}</p>
          <h2>{controlMode ? "채널 제어" : "채널별 모니터링"}</h2>
          <p>{sid} 서버의 등록 채널, 현재 상태와 당일 메시지 흐름을 함께 확인합니다.</p>
        </div>
        <button className="secondary-button" onClick={() => void load()} disabled={loading}>새로고침</button>
      </header>

      <div className="feature-toolbar">
        <label className="search-field">
          <span>검색</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="채널명, 시스템, 상태" />
        </label>
        {controlMode && (
          <div className="control-actions">
            <button onClick={() => void control("CHECK")} disabled={!selected.length || working}>상태 확인</button>
            <button onClick={() => void control("START")} disabled={!selected.length || working || !canControl}>선택 시작</button>
            <button className="danger" onClick={() => void control("STOP")} disabled={!selected.length || working || !canControl}>선택 중지</button>
          </div>
        )}
      </div>

      {notice && <p className="inline-notice">{notice}</p>}
      <div className="feature-split">
        <div className="table-card">
          <div className="table-caption"><b>{filtered.length} channels</b><span>{selected.length} selected</span></div>
          <div className={`data-table ${controlMode ? "channel-control-table" : "channel-table"}`}>
            <div className="data-row data-head">
              {controlMode && <span />}
              <span>채널</span><span>등록 시스템</span><span>방향</span><span>상태</span><span />
            </div>
            {loading ? <p className="empty-state">채널을 불러오는 중입니다.</p> : filtered.map((row) => {
              const rowKey = keyOf(row);
              return (
                <div className="data-row" key={rowKey}>
                  {controlMode && (
                    <span><input type="checkbox" checked={selected.includes(rowKey)} onChange={() => setSelected((current) => current.includes(rowKey) ? current.filter((key) => key !== rowKey) : [...current, rowKey])} aria-label={`${row.channel_id} 선택`} /></span>
                  )}
                  <span><b>{row.channel_id}</b><small>{sid}</small></span>
                  <span>{row.component_id}</span>
                  <span>{row.direction ?? "—"}</span>
                  <span><i className={`status-pill ${String(row.status ?? "unknown").toLowerCase()}`}>{row.status ?? "Unknown"}</i></span>
                  <span><button className="row-action" onClick={() => void openChannel(row)}>상세</button></span>
                </div>
              );
            })}
            {!loading && !filtered.length && <p className="empty-state">조건에 맞는 채널이 없습니다.</p>}
          </div>
        </div>

        <aside className="detail-card">
          {detail ? (
            <>
              <p className="kicker">CHANNEL DETAIL</p>
              <h3>{detail.channel_id}</h3>
              <p className="detail-subtitle">{detail.component_id}</p>
              <div className="mini-metrics">
                <div><span>오늘 처리</span><b>{statistics.total_count.toLocaleString()}</b></div>
                <div><span>실패</span><b>{statistics.fail_count.toLocaleString()}</b></div>
                <div><span>평균 응답</span><b>{statistics.avg_elapsed_sec.toFixed(3)}초</b></div>
              </div>
              <h4>최근 메시지</h4>
              <div className="compact-list">
                {history.map((message) => (
                  <div key={message.log_id}>
                    <span><b>{message.message_id}</b><small>{message.start_time ? new Date(message.start_time).toLocaleString("ko-KR") : "—"}</small></span>
                    <i className={`status-pill ${message.status === "F" ? "error" : "running"}`}>{message.status}</i>
                  </div>
                ))}
                {!history.length && <p className="empty-state">표시할 메시지가 없습니다.</p>}
              </div>
              <details>
                <summary>채널 속성 보기</summary>
                <dl className="attribute-list">
                  {Object.entries(detail.attributes).slice(0, 20).map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{String(value ?? "")}</dd></div>)}
                </dl>
              </details>
            </>
          ) : (
            <div className="detail-empty"><span>⌁</span><b>채널을 선택하세요</b><p>상세 설정, 당일 통계와 최근 메시지가 이 영역에 표시됩니다.</p></div>
          )}
        </aside>
      </div>
    </section>
  );
}
