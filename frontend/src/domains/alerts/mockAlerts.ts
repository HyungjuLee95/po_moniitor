import type { AlertItem } from "./types";

export const mockAlerts: AlertItem[] = [
  {
    id: "ALT-20260728-001",
    sid: "POP",
    title: "Receiver Channel 응답 지연",
    domain: "channels",
    detail: "ERP_ORDER_IN 채널의 평균 응답시간이 임계값 3초를 초과했습니다.",
    severity: "critical",
    status: "open",
    occurredAt: "방금 전",
  },
  {
    id: "ALT-20260728-002",
    sid: "POP",
    title: "메시지 재시도 증가",
    domain: "messages",
    detail: "최근 15분 동안 재시도 메시지가 평소 대비 2.4배 증가했습니다.",
    severity: "warning",
    status: "open",
    occurredAt: "8분 전",
  },
  {
    id: "ALT-20260728-003",
    sid: "POQ",
    title: "Collector 동기화 완료",
    domain: "collectors",
    detail: "지연되었던 수집 구간이 정상적으로 복구되었습니다.",
    severity: "info",
    status: "resolved",
    occurredAt: "32분 전",
  },
];
