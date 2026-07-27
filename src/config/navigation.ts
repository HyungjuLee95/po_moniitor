import type { Role, ViewId } from "../types";

export type NavigationItem = {
  id: ViewId;
  label: string;
  shortLabel: string;
  roles?: Role[];
};

export const navigation: NavigationItem[] = [
  { id: "overview", label: "운영 현황", shortLabel: "OV" },
  { id: "channels", label: "채널 모니터", shortLabel: "CH" },
  { id: "messages", label: "메시지 추적", shortLabel: "MS" },
  { id: "interfaces", label: "인터페이스", shortLabel: "IF" },
  { id: "incidents", label: "인시던트", shortLabel: "IN" },
  { id: "collectors", label: "Collector", shortLabel: "CO", roles: ["ADMIN", "OPERATOR"] },
  { id: "settings", label: "환경 설정", shortLabel: "ST", roles: ["ADMIN"] },
];

export function navigationFor(role: Role): NavigationItem[] {
  return navigation.filter((item) => !item.roles || item.roles.includes(role));
}
