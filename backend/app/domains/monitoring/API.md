# Monitoring API

| Method | Path | Permission | 원본 |
|---|---|---|---|
| GET | `/api/v1/monitoring/summary` | `monitoring:read` | SAP/RTIMS |
| GET | `/api/v1/monitoring/throughput?sid=&granularity=hour&days=1` | `monitoring:read` + SID 접근 권한 | RTIMS MON_MSG_LOG |
| GET | `/api/v1/monitoring/performance` | `monitoring:read` | RTIMS |
| GET | `/api/v1/monitoring/slow-messages` | `monitoring:read` | RTIMS MON_MSG_LOG |
| GET | `/api/v1/monitoring/resources` | `monitoring:read` | RTIMS MON_RES_USAGE |
| GET | `/api/v1/monitoring/queues` | `monitoring:read` | RTIMS Queue |
| GET | `/api/v1/monitoring/system-statistics` | `monitoring:read` | RTIMS 통계·PM 그룹 |
| GET | `/api/v1/monitoring/system-queue-status` | `monitoring:read` | RTIMS MON_Q_STATUS |

`summary`는 `messages_today`, `success_rate`, `failed_messages`, `pending_messages`, `average_latency_ms`, `latency_window_minutes`를 반환한다.

`throughput` 계약:

- `granularity=hour`(기본): Oracle 서버 날짜의 `00:00:00 이상, 다음 날 00:00:00 미만`을 1시간 단위로 집계한다. `days`는 무시하고 meta에는 `1`을 반환한다.
- `granularity=day`: 오늘을 포함한 `days`일을 일 단위로 집계한다. `days` 허용 범위는 `1~31`이며 대시보드는 `7`을 사용한다.
- 각 row는 `bucket`, `label`, `hour`, `total_count`, `success_count`, `fail_count`, `pending_count`, `total_size_bytes`를 반환한다.
- `total_size_bytes`는 `sum(nvl(req_msg_size, 0) + nvl(res_msg_size, 0))`이다.
- 여러 SID 합산은 권한 검증을 유지하기 위해 프론트가 SID별 API를 각각 호출한 뒤 같은 `bucket`끼리 합산한다.
