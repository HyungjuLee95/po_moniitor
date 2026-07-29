export type WidgetId =
  | "health"
  | "throughput"
  | "system_results"
  | "queue_status"
  | "live_interfaces"
  | "daily_checks"
  | "channel_status"
  | "incidents"
  | "server_profile";

export type DashboardDensity = "comfortable" | "compact";

export type DashboardLayout = {
  order: WidgetId[];
  hidden: WidgetId[];
  density: DashboardDensity;
  favorite_views: string[];
  recent_views: string[];
  view_usage: Record<string, number>;
};

export type WidgetDefinition = {
  id: WidgetId;
  name: string;
  description: string;
};
