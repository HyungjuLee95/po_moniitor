# Monitoring API

| 화면 | API |
|---|---|
| 대시보드 | `/monitoring/summary`, `/monitoring/slow-messages` |
| 메시지 트래픽 | `/monitoring/throughput?sid=&granularity=hour\|day&days=1\|7` |
| 성능·리소스 | `/monitoring/performance`, `/resources`, `/queues` |
| 시스템 통계·대기 | `/monitoring/system-statistics`, `/system-queue-status` |
| 실시간 인터페이스 | `/messages?sid=&hours=&status=&keyword=` |

트래픽 위젯은 기본으로 접근 가능한 POP와 PMP를 각각 호출해 같은 bucket을 합산한다. 서버 필터를 고르면 해당 SID만 호출한다. 시간 모드는 `granularity=hour&days=1`, 일 모드는 `granularity=day&days=7`을 사용한다. row의 `total_count`와 `total_size_bytes`는 hover tooltip에 표시한다.
