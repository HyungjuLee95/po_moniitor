export type AlertSeverity = "critical" | "warning" | "info";
export type AlertStatus = "open" | "acknowledged" | "resolved";

export type AlertItem = {
  id: string;
  sid: string;
  title: string;
  domain: string;
  detail: string;
  severity: AlertSeverity;
  status: AlertStatus;
  occurredAt: string;
};
