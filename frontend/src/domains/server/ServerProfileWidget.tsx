import type { PoServer } from "../../core/types";
import { PanelHeader } from "../dashboard/PanelHeader";

export function ServerProfileWidget({ server, connected }: { server?: PoServer; connected: boolean }) {
  return (
    <article className="surface server-profile">
      <PanelHeader eyebrow="ACTIVE SERVER" title={server?.display_name ?? "서버 선택"} action={connected ? "LIVE" : "DEMO"} />
      <div className="server-hero">
        <div className={`server-orbit ${connected ? "online" : ""}`}><span>{server?.sid ?? "--"}</span></div>
        <div><b>{connected ? "API 연결 정상" : "데모 데이터 표시 중"}</b><small>{server?.environment ?? "configuration"}</small></div>
      </div>
      <dl>
        <div><dt>Environment</dt><dd>{server?.environment ?? "-"}</dd></div>
        <div><dt>Capabilities</dt><dd>{server?.capabilities.length ?? 0}</dd></div>
        <div><dt>Configuration</dt><dd>PO_SERVERS_JSON</dd></div>
      </dl>
    </article>
  );
}
