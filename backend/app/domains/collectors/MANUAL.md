# Collectors MANUAL
작은 page, 안정 정렬, 실행 잠금, 성공 범위 checkpoint를 기본으로 한다. Oracle profile은 HANA를 `(timestamp, message_id)`로 오름차순 조회하고 최대 `limit`건만 처리한다. Oracle buffer 적재와 가공 프로시저가 모두 성공한 뒤 같은 transaction에서 checkpoint를 전진한다. 메시지 원문은 PostgreSQL에 복제하지 않는다.

## 자동 실행 환경 변수

| 환경 변수 | 기본값 | 범위 | 의미 |
|---|---:|---:|---|
| `RTIMS_COLLECTOR_ENABLED` | `false` | boolean | `true`일 때만 백그라운드 스케줄러 시작 |
| `RTIMS_COLLECTOR_STARTUP_DELAY_SECONDS` | `30` | 0~3600 | backend 시작 후 최초 실행까지 대기 |
| `RTIMS_COLLECTOR_INTERVAL_SECONDS` | `300` | 30~86400 | profile 없는 호환 경로의 고정 지연 |
| `RTIMS_COLLECTOR_LIMIT` | `500` | 100~5000 | profile 없는 호환 경로의 조회 상한 |
| `RTIMS_COLLECTOR_ORACLE_USER` | 빈 값 | 문자열 | 별도 Collector Oracle 계정, 비면 runtime 계정 사용 |
| `RTIMS_COLLECTOR_ORACLE_PASSWORD` | 빈 값 | secret | 별도 Collector Oracle 비밀번호 |

자동 실행 대상은 `PO_SERVERS_JSON`에서 `enabled=true`이고 `collector` capability가 있는 서버다. `collectors` 배열이 있으면 profile별 Oracle 경로를 사용하며 `interval_seconds`, `limit`, `initial_lookback_seconds`, `pending_search_minutes`, `delivery_semantics`, HANA 연결과 schema를 독립 설정한다. 서버와 profile은 순차 실행하며 한 profile 실패는 Oracle 오류 로그를 시도한 뒤 다음 profile로 진행한다. 종료 event는 시작 지연과 주기 대기를 즉시 중단한다.

매 주기는 신규 page와 별도로 Oracle `MON_MSG_LOG`의 1분 이상 된 Pending ID를 최대 `limit`건 읽어 HANA 상태를 다시 확인한다. HANA ID 목록과 반환 row에도 같은 상한을 적용한다. 이 상태 갱신 row는 buffer 처리에는 포함하지만 신규 page checkpoint를 전진시키지 않는다.

profile 필수 필드는 `collector_id`, 전역에서 유일한 `oracle_instance_id`, `delivery_semantics=BE|EO`, `po_db_schema`다. `hana_host/user/password/port`는 profile 값을 우선하며 비어 있으면 공통 `SAP_HANA_*` 값을 사용한다. `host_id_table`과 `host_id_field`는 둘을 함께 지정한다. 식별자는 검증 후 SQL에 조립되고 checkpoint와 시간은 bind parameter로 전달된다.

운영 적용 순서는 다음과 같다.

1. 기존 RTIMS Oracle에 `MON_BUF_AAE_MSG`, `MON_AAE_SEQ_ID`, `MON_COLLECTOR_PARAMS`, `MON_COLLECTOR_LOG`, `MON_COL_LOG_ID`, `process_msg_logs`가 있는지 DBA가 확인한다.
2. HANA 계정에 대상 schema의 `bc_msg_log`(BE), `bc_msg`(EO), 선택 host table의 SELECT만 부여한다.
3. Collector Oracle 계정에 buffer·runtime parameter·log DML, 두 sequence 사용, `process_msg_logs` 실행 최소 권한을 부여한다.
4. 처음에는 `RTIMS_COLLECTOR_ENABLED=false`로 backend를 시작하고 관리자 수동 실행 API로 한 profile·작은 limit을 검증한다.
5. 건수·시간대·중복·프로시저 결과·checkpoint 불변을 확인한 뒤 자동 실행을 켠다.

현재 제공되는 `setup-rtims-databases`의 14개 객체 호환 DDL은 조회 화면용이며 위 Collector 전체 객체와 프로시저를 생성하지 않는다. 기존 전체 RTIMS schema 또는 DBA가 검증한 원본 Collector DDL이 필요하다. Collector scheduler를 실행하는 backend 인스턴스는 하나만 둔다.

Legacy의 선택적 `ENABLE_SYNC` 누락 메시지 복구 경로(`MON_BUF_AAE_SYNC`, `process_insert_aaemsgsync`)는 현재 profile에 포함하지 않는다. 해당 기능이 실제 운영에서 켜져 있었다면 관련 DDL·프로시저와 실행 주기를 확인한 뒤 별도 profile 기능으로 추가한다.
