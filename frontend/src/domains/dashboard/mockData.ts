import type { ChannelRow, MonitoringSummary, PoServer } from "../../core/types";

export const fallbackServers: PoServer[] = [
  { sid: "POP", display_name: "PO Production", environment: "production", enabled: true, capabilities: ["monitor", "channel-control", "collector"] },
  { sid: "POQ", display_name: "PO Quality", environment: "quality", enabled: true, capabilities: ["monitor", "collector"] },
  { sid: "POD", display_name: "PO Development", environment: "development", enabled: true, capabilities: ["monitor", "collector", "hrd"] },
];

export const fallbackSummary: MonitoringSummary = {
  sid: "POP",
  server_name: "PO Production",
  channels: { total: 128, running: 121, error: 3, stopped: 4 },
  messages_today: 284391,
  success_rate: 99.72,
  average_latency_ms: 842,
  source: "demo",
};

export const fallbackChannels: ChannelRow[] = [
  { id: 1, sid: "POP", component_id: "BC_ERP_ORDER", channel_id: "ERP_ORDER_IN", direction: "Receiver", status: "Error", latency_ms: 4280 },
  { id: 2, sid: "POP", component_id: "BC_MES_RESULT", channel_id: "MES_RESULT_OUT", direction: "Sender", status: "Running", latency_ms: 621 },
  { id: 3, sid: "POP", component_id: "BC_HR_MASTER", channel_id: "HR_MASTER_IN", direction: "Receiver", status: "Running", latency_ms: 384 },
  { id: 4, sid: "POP", component_id: "BC_WMS_STOCK", channel_id: "WMS_STOCK_OUT", direction: "Sender", status: "Stopped", latency_ms: null },
];
