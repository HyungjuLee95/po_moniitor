# Collectors SKILL
SAP 부하를 고려해 page size·window·동시성을 설정 가능하게 한다. 실패 범위는 checkpoint로 확정하지 않는다.

- 자동 실행은 opt-in 환경 변수와 FastAPI lifespan에서만 시작한다.
- 시작 지연과 실행 간격은 `Event.wait()`로 대기해 종료 시 즉시 깨울 수 있어야 한다.
- SID·profile은 순차 실행하고 프로세스 내부 `(SID, collector_id)` lock을 수동 API와 공유한다.
- Oracle profile의 checkpoint 원본은 `MON_COLLECTOR_PARAMS`이며 PostgreSQL checkpoint와 혼용하지 않는다.
- HANA 조회는 `(timestamp, message_id)` 안정 정렬, bind, bounded TOP을 보존한다.
- buffer insert, `process_msg_logs`, checkpoint와 성공 로그의 단일 Oracle transaction을 분리하지 않는다.
- 외부 호출 오류에는 SID만 기록하고 URL·계정·payload는 로그에 남기지 않는다.
- 전체 Collector DDL·프로시저가 확인되지 않은 새 schema를 운영 호환으로 표시하지 않는다.
- 분산 잠금이 구현되기 전 scheduler 활성 backend를 여러 개 실행하지 않는다.
