import type { DashboardLayout, WidgetDefinition } from "./types";

export const widgets: WidgetDefinition[] = [
  { id: "health", name: "운영 핵심 지표", description: "채널·메시지·오류·응답시간 요약" },
  { id: "throughput", name: "메시지 처리량", description: "24시간 메시지 처리 추이" },
  { id: "channel_status", name: "채널 상태", description: "주요 채널과 현재 상태" },
  { id: "incidents", name: "최근 장애", description: "확인이 필요한 장애 목록" },
  { id: "server_profile", name: "서버 프로필", description: "선택 서버의 환경과 기능" },
];

export const defaultDashboardLayout: DashboardLayout = {
  order: widgets.map((widget) => widget.id),
  hidden: [],
  density: "comfortable",
};
