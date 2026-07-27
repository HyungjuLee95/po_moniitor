export type WidgetId =
  | "health"
  | "throughput"
  | "channel_status"
  | "incidents"
  | "server_profile";

export type DashboardDensity = "comfortable" | "compact";

export type DashboardLayout = {
  order: WidgetId[];
  hidden: WidgetId[];
  density: DashboardDensity;
};

export type WidgetDefinition = {
  id: WidgetId;
  name: string;
  description: string;
};
