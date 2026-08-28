# Collectors API

`GET /api/v1/collectors`는 상태와 checkpoint, `POST /api/v1/collectors/run`은 SID별 수동 수집을 제공한다. 각각 `collectors:read`, `collectors:run` 권한과 `collector` capability를 사용한다.

`GET /api/v1/collectors`의 `meta`는 `automatic_enabled`, `startup_delay_seconds`, 호환 기본 `interval_seconds/limit`, `pipeline`, `profile_count`, `oracle_configured`를 반환한다. Oracle profile의 상태·checkpoint·마지막 로그는 Oracle `MON_COLLECTOR_PARAMS/LOG`에서 조회한다. 비밀값이나 내부 URL은 포함하지 않는다.

`pipeline=sap-po-hana-to-rtims-oracle`은 하나 이상의 활성 profile이 있음을 뜻한다. `pipeline=sap-po-message-checkpoint`는 profile 없는 서버의 SAP PO 조회·PostgreSQL checkpoint 호환 경로다.

`POST /api/v1/collectors/run` body는 `sids[]`와 선택적 `collector_ids[]`를 받는다. profile 경로는 신규 HANA page와 Pending 상태 재조회 후 Oracle 적재·프로시저·checkpoint를 순차 실행하며 `fetched`, `new_rows`, `status_rows`를 반환한다. 자동 스케줄러가 OFF여도 Oracle 연결정보가 있으면 수동 실행할 수 있다.
