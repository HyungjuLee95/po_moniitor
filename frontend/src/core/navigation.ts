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
  | "operations"
  | "administration";

export const navigationCategories: Array<{ id: NavigationCategory; label: string }> = [
  { id: "status", label: "현황" },
  { id: "operations", label: "운영" },
  { id: "analysis", label: "분석" },
  { id: "administration", label: "관리" },
];

export const navigation: NavigationItem[] = [
  { id: "overview", label: "운영 대시보드", eyebrow: "OVERVIEW", glyph: "01", category: "status" },
  { id: "realtime_interfaces", label: "실시간 인터페이스", eyebrow: "LIVE INTERFACE", glyph: "02", category: "status" },
  { id: "system_status", label: "시스템별 처리 결과", eyebrow: "SYSTEM RESULT", glyph: "03", category: "status" },
  { id: "performance", label: "리소스 조회", eyebrow: "RESOURCE", glyph: "04", category: "status" },
  { id: "incidents", label: "장애·알림", eyebrow: "INCIDENTS", glyph: "05", category: "status" },
  { id: "certificates", label: "인증서 만료 현황", eyebrow: "CERTIFICATE", glyph: "06", category: "status", roles: ["ADMIN", "OPERATOR"] },
  { id: "channels", label: "채널 상태", eyebrow: "CHANNEL STATUS", glyph: "07", category: "operations" },
  { id: "interfaces", label: "시스템 별 채널 정보", eyebrow: "SYSTEM CHANNEL", glyph: "08", category: "operations" },
  { id: "channel_control", label: "채널 컨트롤", eyebrow: "CHANNEL CONTROL", glyph: "09", category: "operations", roles: ["ADMIN", "OPERATOR"] },
  { id: "channel_bulk", label: "채널 대량 변경", eyebrow: "BULK EXCEL", glyph: "10", category: "operations", roles: ["ADMIN"] },
  { id: "hrd", label: "HRD 인터페이스 조회", eyebrow: "HRD LOOKUP", glyph: "11", category: "operations" },
  { id: "hrd_test", label: "HRD 테스트 메시지", eyebrow: "HRD TEST", glyph: "12", category: "operations", roles: ["ADMIN", "OPERATOR"] },
  { id: "daily_checks", label: "HRD·Delivering 점검", eyebrow: "DAILY CHECK", glyph: "13", category: "operations" },
  { id: "oracle_ifs", label: "Oracle IFS", eyebrow: "IFS SYNC", glyph: "14", category: "operations" },
  { id: "messages", label: "CC 로그 조회", eyebrow: "MESSAGE TRACE", glyph: "15", category: "analysis" },
  { id: "audit", label: "MessageID 조회", eyebrow: "AUDIT LOOKUP", glyph: "16", category: "analysis" },
  { id: "topology", label: "시스템 연결 관계", eyebrow: "TOPOLOGY", glyph: "17", category: "analysis" },
  { id: "namespaces", label: "Namespace 인벤토리", eyebrow: "NAMESPACE", glyph: "18", category: "analysis" },
  { id: "workspaces", label: "워크스페이스", eyebrow: "WORKSPACE", glyph: "19", category: "administration" },
  { id: "posts", label: "운영 지식 게시글", eyebrow: "KNOWLEDGE", glyph: "20", category: "administration" },
  { id: "account", label: "내 계정", eyebrow: "ACCOUNT", glyph: "21", category: "administration" },
  { id: "settings", label: "사용자·환경 설정", eyebrow: "SETTINGS", glyph: "22", category: "administration", roles: ["ADMIN"] },
];

export function navigationFor(role: Role): NavigationItem[] {
  return navigation.filter((item) => !item.roles || item.roles.includes(role));
}
