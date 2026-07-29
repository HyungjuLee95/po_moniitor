import type { DashboardLayout, WidgetDefinition } from "./types";

export const widgets: WidgetDefinition[] = [
  { id: "health", name: "운영 핵심 지표", description: "메시지량·성공률·실패·응답시간 요약" },
  { id: "throughput", name: "메시지 처리량", description: "24시간 메시지 처리 추이" },
  { id: "system_results", name: "시스템별 처리 결과", description: "시스템 그룹별 성공·실패·Delivering" },
  { id: "queue_status", name: "Queue·Thread", description: "Adapter Engine과 시스템 Queue 상태" },
  { id: "live_interfaces", name: "실시간 인터페이스", description: "최근 처리 인터페이스 흐름" },
  { id: "daily_checks", name: "일일 점검", description: "HRD 현행과 7일 Delivering 점검" },
  { id: "channel_status", name: "채널 상태", description: "주요 채널과 현재 상태" },
  { id: "incidents", name: "최근 장애", description: "확인이 필요한 장애 목록" },
  { id: "server_profile", name: "서버 프로필", description: "선택 서버의 환경과 기능" },
];

export const defaultDashboardLayout: DashboardLayout = {
  order: widgets.map((widget) => widget.id),
  hidden: ["channel_status", "server_profile"],
  density: "comfortable",
  favorite_views: [],
  recent_views: [],
  view_usage: {},
};
