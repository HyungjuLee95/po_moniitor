export type Role = "ADMIN" | "OPERATOR" | "VIEWER";
export type ViewId =
  | "overview"
  | "realtime_interfaces"
  | "channels"
  | "channel_control"
  | "channel_bulk"
  | "messages"
  | "audit"
  | "interfaces"
  | "performance"
  | "topology"
  | "incidents"
  | "collectors"
  | "workspaces"
  | "settings"
  | "hrd"
  | "hrd_test"
  | "daily_checks"
  | "namespaces"
  | "system_status"
  | "oracle_ifs"
  | "posts"
  | "account";

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
  failed_messages: number;
  pending_messages: number;
  success_rate: number;
  average_latency_ms: number;
  latency_window_minutes: number;
  source: string;
};

export type MonitoringPolicy = {
  sid: string;
  response_window_minutes: number;
  slow_threshold_ms: number;
  critical_threshold_ms: number;
  max_detail_rows: number;
  updated_by?: string | null;
};

export type SlowMessage = {
  log_id: number;
  message_id: string;
  status: string;
  start_time: string | null;
  elapsed_sec: number;
  interface_name: string | null;
  source_system: string | null;
  target_system: string | null;
};

export type ManagedUser = {
  username: string;
  display_name: string;
  role: Role;
  active: boolean;
  first_login: boolean;
  server_sids: string[];
};

export type ChannelRow = {
  id: number;
  sid: string;
  component_id: string;
  channel_id: string;
  direction: string;
  status: "Running" | "Error" | "Stopped";
  latency_ms: number | null;
  adapter_type?: string;
  automation?: string;
  raw_status?: string;
};

export type ChannelInventoryRow = Partial<ChannelRow> & {
  id: number;
  sid: string;
  component_id: string;
  channel_id: string;
  party_id?: string;
};

export type ChannelStatistics = {
  total_count: number;
  success_count: number;
  fail_count: number;
  pending_count: number;
  avg_elapsed_sec: number;
  total_msg_size: number;
  avg_msg_size: number;
};

export type ChannelMessage = {
  log_id: number;
  message_id: string;
  status: string;
  server_id: string;
  start_time: string | null;
  elapsed_sec: number;
  msg_size: number;
};

export type MessageRow = {
  message_id: string;
  sid: string;
  interface_name: string;
  namespace?: string;
  status: string;
  start_time: string | null;
  end_time?: string | null;
  duration_ms?: number | null;
  source_system?: string | null;
  target_system?: string | null;
  error_text?: string | null;
};

export type AuditEntry = {
  message_id: string;
  sid: string;
  status: string;
  time: string | null;
  text: string;
};

export type BusinessSystem = {
  sid: string;
  business_system_id: string;
  name: string;
  active: boolean;
};

export type WorkspaceRecord = {
  workspace_id: number;
  task_name: string;
  description: string | null;
  progress: number;
  status: "planned" | "in_progress" | "review" | "completed";
  target_date: string | null;
  created_at: string;
  updated_at: string;
};
