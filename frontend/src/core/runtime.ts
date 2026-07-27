const configuredBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

export const runtimeConfig = {
  apiBaseUrl: (configuredBase || (
    typeof window === "undefined"
      ? "http://127.0.0.1:8000"
      : `${window.location.protocol}//${window.location.hostname}:8000`
  )).replace(/\/+$/, ""),
  apiPrefix: "/api/v1",
  tokenKey: "po-monitor-main.access-token",
  layoutFallbackKey: "po-monitor-main.dashboard-layout",
} as const;
