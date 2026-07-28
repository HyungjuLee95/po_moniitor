import type { Role, ViewId } from "./types";

export type NavigationItem = {
  id: ViewId;
  label: string;
  eyebrow: string;
  glyph: string;
  category: NavigationCategory;
  roles?: Role[];
};

export type NavigationCategory = "status" | "analysis" | "operations" | "administration";

export const navigationCategories: Array<{ id: NavigationCategory; label: string }> = [
  { id: "status", label: "현황" },
  { id: "analysis", label: "추적 · 분석" },
  { id: "operations", label: "운영 도구" },
  { id: "administration", label: "관리" },
];

export const navigation: NavigationItem[] = [
  { id: "overview", label: "통합 대시보드", eyebrow: "OVERVIEW", glyph: "01", category: "status" },
  { id: "channels", label: "채널 모니터링", eyebrow: "CHANNELS", glyph: "02", category: "status" },
  { id: "incidents", label: "장애 관리", eyebrow: "INCIDENTS", glyph: "03", category: "status" },
  { id: "messages", label: "메시지 추적", eyebrow: "MESSAGES", glyph: "04", category: "analysis" },
  { id: "audit", label: "Audit 로그", eyebrow: "AUDIT", glyph: "05", category: "analysis" },
  { id: "interfaces", label: "시스템별 채널", eyebrow: "SYSTEMS", glyph: "06", category: "analysis" },
  { id: "performance", label: "성능·리소스", eyebrow: "PERFORMANCE", glyph: "07", category: "analysis" },
  { id: "topology", label: "시스템 연결 관계", eyebrow: "TOPOLOGY", glyph: "08", category: "analysis" },
  { id: "channel_control", label: "채널 제어", eyebrow: "CONTROL", glyph: "09", category: "operations", roles: ["ADMIN", "OPERATOR"] },
  { id: "workspaces", label: "워크스페이스", eyebrow: "WORKSPACE", glyph: "10", category: "operations" },
  { id: "settings", label: "환경 설정", eyebrow: "SETTINGS", glyph: "11", category: "administration", roles: ["ADMIN"] },
];

export function navigationFor(role: Role): NavigationItem[] {
  return navigation.filter((item) => !item.roles || item.roles.includes(role));
}
