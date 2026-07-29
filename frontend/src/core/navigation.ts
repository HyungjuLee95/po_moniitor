import type { Role, ViewId } from "./types";

export type NavigationItem = {
  id: ViewId;
  label: string;
  eyebrow: string;
  glyph: string;
  category: NavigationCategory;
  roles?: Role[];
};

export type NavigationCategory =
  | "status"
  | "analysis"
  | "channels"
  | "hrd"
  | "operations"
  | "administration";

export const navigationCategories: Array<{ id: NavigationCategory; label: string }> = [
  { id: "status", label: "현황" },
  { id: "analysis", label: "추적 · 분석" },
  { id: "channels", label: "채널 운영" },
  { id: "hrd", label: "HRD 업무" },
  { id: "operations", label: "업무 도구" },
  { id: "administration", label: "관리" },
];

export const navigation: NavigationItem[] = [
  { id: "overview", label: "운영 대시보드", eyebrow: "OVERVIEW", glyph: "01", category: "status" },
  { id: "realtime_interfaces", label: "실시간 인터페이스", eyebrow: "LIVE INTERFACE", glyph: "02", category: "status" },
  { id: "channels", label: "채널 상태 현황", eyebrow: "CHANNEL STATUS", glyph: "03", category: "status" },
  { id: "incidents", label: "장애·알림", eyebrow: "INCIDENTS", glyph: "04", category: "status" },
  { id: "messages", label: "CC 로그 조회", eyebrow: "MESSAGE TRACE", glyph: "05", category: "analysis" },
  { id: "audit", label: "MessageID 조회", eyebrow: "AUDIT LOOKUP", glyph: "06", category: "analysis" },
  { id: "system_status", label: "시스템별 처리 결과", eyebrow: "SYSTEM RESULT", glyph: "07", category: "analysis" },
  { id: "performance", label: "리소스 조회", eyebrow: "RESOURCE", glyph: "08", category: "status" },
  { id: "topology", label: "시스템 연결 관계", eyebrow: "TOPOLOGY", glyph: "09", category: "analysis" },
  { id: "namespaces", label: "Namespace 인벤토리", eyebrow: "NAMESPACE", glyph: "10", category: "analysis" },
  { id: "interfaces", label: "시스템 별 채널 정보", eyebrow: "SYSTEM CHANNEL", glyph: "11", category: "channels" },
  { id: "channel_control", label: "채널 컨트롤", eyebrow: "CHANNEL CONTROL", glyph: "12", category: "channels", roles: ["ADMIN", "OPERATOR"] },
  { id: "channel_bulk", label: "채널 대량 변경", eyebrow: "BULK EXCEL", glyph: "13", category: "channels", roles: ["ADMIN"] },
  { id: "hrd", label: "HRD 인터페이스 조회", eyebrow: "HRD LOOKUP", glyph: "14", category: "hrd" },
  { id: "hrd_test", label: "HRD 테스트 메시지", eyebrow: "HRD TEST", glyph: "15", category: "hrd", roles: ["ADMIN", "OPERATOR"] },
  { id: "daily_checks", label: "HRD·Delivering 일일 점검", eyebrow: "DAILY CHECK", glyph: "16", category: "hrd" },
  { id: "workspaces", label: "워크스페이스", eyebrow: "WORKSPACE", glyph: "17", category: "operations" },
  { id: "oracle_ifs", label: "Oracle IFS", eyebrow: "IFS SYNC", glyph: "18", category: "operations" },
  { id: "posts", label: "운영 지식 게시글", eyebrow: "KNOWLEDGE", glyph: "19", category: "operations" },
  { id: "account", label: "내 계정", eyebrow: "ACCOUNT", glyph: "20", category: "administration" },
  { id: "settings", label: "사용자·환경 설정", eyebrow: "SETTINGS", glyph: "21", category: "administration", roles: ["ADMIN"] },
];

export function navigationFor(role: Role): NavigationItem[] {
  return navigation.filter((item) => !item.roles || item.roles.includes(role));
}
