export type Role = "ADMIN" | "OPERATOR" | "VIEWER";

export type User = {
  username: string;
  display_name: string;
  role: Role;
  permissions: string[];
};

export type PoServer = {
  sid: string;
  display_name: string;
  environment: "production" | "quality" | "development" | "sandbox";
  enabled: boolean;
  capabilities: string[];
};

export type Bootstrap = {
  application: { name: string; version: string; mode: "demo" | "live" };
  current_user: User;
  servers: PoServer[];
};

export type MonitoringSummary = {
  sid: string;
  server_name: string;
  channels: { total: number; running: number; error: number; stopped: number };
  messages_today: number;
  success_rate: number;
  average_latency_ms: number;
  source: string;
};

export type ChannelRow = {
  id: number;
  sid: string;
  component_id: string;
  channel_id: string;
  direction: "Sender" | "Receiver";
  status: "Running" | "Error" | "Stopped";
  latency_ms: number | null;
};

export type ViewId =
  | "overview"
  | "channels"
  | "messages"
  | "interfaces"
  | "incidents"
  | "collectors"
  | "settings";
