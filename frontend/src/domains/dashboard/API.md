# Dashboard API

## Client request contract

Dashboard consumers use `DASHBOARD_REQUEST_TIMEOUT_MS=12000`. A timeout affects only its own request. Initial loads fall back safely, while background refreshes keep the last successful response.

위젯 데이터는 `/monitoring/summary`, `/monitoring/throughput`, `/monitoring/system-statistics`, `/monitoring/queues`, `/messages`, `/hrd/interfaces`, `/alerts`를 사용한다.

트래픽 위젯은 `/monitoring/throughput`을 접근 가능한 POP/PMP SID별로 호출하며, 프론트에서 bucket 기준으로 합산한다. API 계약의 `granularity`, `days`, `total_size_bytes`는 monitoring 도메인 `API.md`를 따른다.

`GET/PUT /dashboard/preferences`는 위젯 `order/hidden/density`와 메뉴 `favorite_views/recent_views/view_usage`를 사용자별로 저장한다. 이전 형식에는 새 위젯과 메뉴 필드를 기본값으로 보충한다.

대시보드 데이터 API는 하나의 `Promise.all`로 묶지 않는다. 각 소비자가 독립적으로 최초 응답을 반영하고, 화면이 유지되는 동안 15분마다 stale-while-revalidate 방식으로 다시 호출한다. 갱신 실패 시 기존 성공 데이터를 유지한다.
