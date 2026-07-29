"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiFetch, apiRequest } from "../../core/api";
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
  mode = "monitor",
}: {
  sid: string;
  server?: PoServer;
  user: User;
  mode?: "monitor" | "control" | "bulk";
}) {
  const controlMode = mode === "control";
  const bulkMode = mode === "bulk";
  const [rows, setRows] = useState<ChannelInventoryRow[]>([]);
  const [query, setQuery] = useState("");
  const [systemFilter, setSystemFilter] = useState("");
  const [channelKind, setChannelKind] = useState<"all" | "standard" | "scheduled">("all");
  const [selected, setSelected] = useState<string[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [statistics, setStatistics] = useState<ChannelStatistics>(emptyStats);
  const [history, setHistory] = useState<ChannelMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [notice, setNotice] = useState("");
  const [batchList, setBatchList] = useState("");
  const [batchProgress, setBatchProgress] = useState("");
  const [preview, setPreview] = useState<{ total: number; to_change: number; errors: string[]; details: Array<{ row: number; channel: string; changes: string[] }> } | null>(null);

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
    return rows.filter((row) => {
      const scheduled = String(row.automation ?? "").toUpperCase().includes("SCHEDUL");
      const matchesKind = channelKind === "all"
        || (channelKind === "scheduled" ? scheduled : !scheduled);
      const matchesSystem = !systemFilter || row.component_id === systemFilter;
      const matchesQuery = !normalized || (
        row.channel_id.toLowerCase().includes(normalized)
        || row.component_id.toLowerCase().includes(normalized)
        || String(row.status ?? "").toLowerCase().includes(normalized)
      );
      return matchesKind && matchesSystem && matchesQuery;
    });
  }, [channelKind, query, rows, systemFilter]);
  const systems = useMemo(
    () => [...new Set(rows.map((row) => row.component_id))].sort(),
    [rows],
  );

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

  const streamControl = async (action: string) => {
    if (!batchList.trim() || !canControl) return;
    setWorking(true); setBatchProgress(""); setNotice("");
    try {
      const response = await apiRequest("/channels/batch-control-stream", {
        method: "POST",
        body: JSON.stringify({ sid, action, channel_list: batchList, mode: "MASS" }),
      });
      const reader = response.body?.getReader();
      if (!reader) throw new Error("stream unavailable");
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        for (const event of events) {
          const line = event.split("\n").find((item) => item.startsWith("data: "));
          if (!line) continue;
          const payload = JSON.parse(line.slice(6)) as { type: string; current?: number; total?: number; data?: { succeeded?: number; failed?: number }; message?: string };
          if (payload.type === "progress") setBatchProgress(`${payload.current} / ${payload.total} 처리 중`);
          if (payload.type === "complete") setNotice(`일괄 제어 완료 · 성공 ${payload.data?.succeeded ?? 0} / 실패 ${payload.data?.failed ?? 0}`);
          if (payload.type === "error") setNotice(payload.message || "일괄 제어 실패");
        }
      }
      await load();
    } catch {
      setNotice("일괄 제어 스트림을 처리하지 못했습니다.");
    } finally { setWorking(false); }
  };

  const exportChannels = async () => {
    try {
      const response = await apiRequest(`/channels/bulk-export?sid=${encodeURIComponent(sid)}&component_id=${encodeURIComponent(systemFilter || "*")}&channel_pattern=*`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `Channels_${sid}.xlsx`; anchor.click();
      URL.revokeObjectURL(url);
    } catch { setNotice("채널 Excel 추출에 실패했습니다. admin 권한을 확인하세요."); }
  };

  const previewFile = async (file?: File) => {
    if (!file) return;
    const form = new FormData(); form.append("sid", sid); form.append("file", file);
    try {
      const response = await apiRequest("/channels/bulk-preview", { method: "POST", body: form });
      const payload = await response.json() as { data: typeof preview };
      setPreview(payload.data);
    } catch { setNotice("채널 변경 미리보기에 실패했습니다."); }
  };

  return (
    <section className="feature-page">
      <header className="feature-header">
        <div>
          <p className="kicker">{bulkMode ? "CHANNEL BULK EXCEL" : (controlMode ? "CHANNEL CONTROL" : "CHANNEL OBSERVABILITY")}</p>
          <h2>{bulkMode ? "채널 대량 변경" : (controlMode ? "채널 컨트롤" : "채널 상태 현황")}</h2>
          <p>{bulkMode ? "비즈니스 시스템별 채널 설정을 Excel로 추출하고 변경 내용을 적용 전 미리 확인합니다." : `${sid} 서버의 등록 채널, 현재 상태와 당일 메시지 흐름을 함께 확인합니다.`}</p>
        </div>
        <button className="secondary-button" onClick={() => void load()} disabled={loading}>새로고침</button>
      </header>

      <div className="feature-toolbar">
        <label className="compact-select">
          <span>비즈니스 시스템</span>
          <select value={systemFilter} onChange={(event) => setSystemFilter(event.target.value)}>
            <option value="">전체 시스템</option>
            {systems.map((system) => <option value={system} key={system}>{system}</option>)}
          </select>
        </label>
        <label className="search-field">
          <span>검색</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="채널명, 시스템, 상태" />
        </label>
        {controlMode && (
          <div className="status-tabs channel-kind-tabs" role="group" aria-label="채널 실행 유형">
            <button className={channelKind === "all" ? "active" : ""} onClick={() => setChannelKind("all")}>전체</button>
            <button className={channelKind === "standard" ? "active" : ""} onClick={() => setChannelKind("standard")}>일반 채널</button>
            <button className={channelKind === "scheduled" ? "active" : ""} onClick={() => setChannelKind("scheduled")}>스케줄 채널</button>
          </div>
        )}
        {controlMode && (
          <div className="control-actions">
            <button onClick={() => void control("CHECK")} disabled={!selected.length || working}>상태 확인</button>
            <button onClick={() => void control("START")} disabled={!selected.length || working || !canControl}>선택 시작</button>
            <button className="danger" onClick={() => void control("STOP")} disabled={!selected.length || working || !canControl}>선택 중지</button>
          </div>
        )}
      </div>

      {notice && <p className="inline-notice">{notice}</p>}
      {controlMode && (
        <section className="bulk-operation-panel">
          <div><p className="kicker">BATCH CONTROL · SSE</p><h3>채널 일괄 제어</h3><p>`등록시스템|채널명`을 한 줄에 하나씩 입력하면 진행률을 실시간으로 표시합니다.</p></div>
          <textarea value={batchList} onChange={(event) => setBatchList(event.target.value)} placeholder={"BS_SYSTEM|CHANNEL_A\nBS_SYSTEM|CHANNEL_B"} />
          <div className="control-actions">
            <button onClick={() => void streamControl("CHECK")} disabled={working || !batchList.trim()}>상태 일괄 확인</button>
            <button onClick={() => void streamControl("START")} disabled={working || !batchList.trim() || !canControl}>일괄 시작</button>
            <button className="danger" onClick={() => void streamControl("STOP")} disabled={working || !batchList.trim() || !canControl}>일괄 중지</button>
          </div>
          {batchProgress && <p className="inline-notice">{batchProgress}</p>}
        </section>
      )}
      {bulkMode && (
        <section className="bulk-operation-panel excel-operation-panel">
          <div><p className="kicker">CHANNEL CONFIGURATION EXCEL</p><h3>Excel 추출·변경 미리보기</h3><p>선택한 비즈니스 시스템의 채널 설정을 내려받고, 수정 파일은 실제 반영 전에 변경점과 오류를 검증합니다.</p></div>
          <div className="control-actions">
            <button onClick={() => void exportChannels()} disabled={user.role !== "ADMIN"}>비즈니스 시스템 Excel 다운로드</button>
            <label className="file-button">수정 Excel 업로드<input type="file" accept=".xlsx" onChange={(event) => void previewFile(event.target.files?.[0])} /></label>
          </div>
          {preview && <details open><summary>변경 미리보기 · {preview.to_change}/{preview.total}건 변경</summary><div className="compact-list">{preview.details.map((item) => <div key={item.row}><span><b>{item.channel}</b><small>{item.changes.join(", ")}</small></span><i>{item.row}행</i></div>)}{preview.errors.map((error) => <p className="form-error" key={error}>{error}</p>)}</div></details>}
        </section>
      )}
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
