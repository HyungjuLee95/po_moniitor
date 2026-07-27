import type { ChannelRow } from "../../core/types";
import { PanelHeader } from "../dashboard/PanelHeader";

export function ChannelStatusWidget({ channels }: { channels: ChannelRow[] }) {
  return (
    <article className="surface channel-card span-two">
      <PanelHeader eyebrow="CHANNEL HEALTH" title="주요 채널 상태" action={`${channels.length} channels`} />
      <div className="data-table">
        <div className="data-row data-head"><span>채널</span><span>컴포넌트</span><span>방향</span><span>응답</span><span>상태</span></div>
        {channels.map((channel) => (
          <div className="data-row" key={channel.id}>
            <span><b>{channel.channel_id}</b><small>{channel.sid}</small></span>
            <span>{channel.component_id}</span>
            <span>{channel.direction}</span>
            <span>{channel.latency_ms == null ? "—" : `${channel.latency_ms}ms`}</span>
            <span><Status value={channel.status} /></span>
          </div>
        ))}
      </div>
    </article>
  );
}

function Status({ value }: { value: ChannelRow["status"] }) {
  return <span className={`status-pill ${value.toLowerCase()}`}><i />{value}</span>;
}
