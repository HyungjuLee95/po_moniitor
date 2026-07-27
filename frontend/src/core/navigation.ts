import type { Role, ViewId } from "./types";

export type NavigationItem = {
  id: ViewId;
  label: string;
  eyebrow: string;
  glyph: string;
  roles?: Role[];
};

export const navigation: NavigationItem[] = [
  { id: "overview", label: "통합 대시보드", eyebrow: "OVERVIEW", glyph: "01" },
  { id: "channels", label: "채널 모니터링", eyebrow: "CHANNELS", glyph: "02" },
  { id: "messages", label: "메시지 추적", eyebrow: "MESSAGES", glyph: "03" },
  { id: "interfaces", label: "인터페이스", eyebrow: "INTERFACES", glyph: "04" },
  { id: "incidents", label: "장애 관리", eyebrow: "INCIDENTS", glyph: "05" },
  { id: "collectors", label: "Collector", eyebrow: "COLLECTORS", glyph: "06", roles: ["ADMIN", "OPERATOR"] },
  { id: "settings", label: "환경 설정", eyebrow: "SETTINGS", glyph: "07", roles: ["ADMIN"] },
];

export function navigationFor(role: Role): NavigationItem[] {
  return navigation.filter((item) => !item.roles || item.roles.includes(role));
}
