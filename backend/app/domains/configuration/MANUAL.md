# Configuration MANUAL
서버 속성은 `PoServer`가 단일 계약이다. `public_view()`에는 SID·표시명·환경·capability만 포함하고 URL·credential을 제외한다. 응답시간 window·지연 기준·상세 건수는 `configuration.monitoring_policy`에서 관리하며 admin만 변경한다.

`PO_SERVERS_JSON`의 서버별 우선순위는 다음과 같다.

1. `base_url`과 `port`로 해당 SID의 origin을 만든다.
2. 서버별 `username`/`password`가 있으면 사용하고, 없거나 빈 값이면 공통 `SAP_PO_USER`/`SAP_PO_PASSWORD`를 사용한다.
3. 서버별 `endpoint_paths`에 작업 경로가 있으면 사용하고, 없으면 대응하는 공통 `SAP_*_PATH` 값을 사용한다.

지원하는 `endpoint_paths` 키는 `channels`, `channel_admin`, `adapter_monitor`, `aae_monitor`, `systatus`, `business_system`, `interface_monitor`, `directory`, `hrd_test`다. 값은 반드시 `/`로 시작해야 하며 내부 host 전체를 넣지 않는다.

운영 모드 시작 시 `.env` registry의 서버 메타데이터를 `configuration.po_server`에 upsert해 사용자별 서버 FK와 동기화한다. 계정·비밀번호는 저장하지 않는다.

LLM 연동 주소는 `LLM_API_URL`, 요청 timeout은 `LLM_API_TIMEOUT_SECONDS`로 설정한다. 두 값은 backend 전용이며 bootstrap과 frontend 환경변수로 복사하지 않는다.

RTIMS runtime은 `RTIMS_ORACLE_USER/PASSWORD`, 신규 schema 생성기는 `RTIMS_ORACLE_DDL_USER/PASSWORD`를 사용한다. 둘 다 backend 전용이며 동일 계정을 강제하지 않는다. 계정이 다르면 `RTIMS_ORACLE_SCHEMA`에 owner를 지정하며 pool acquire 시 안전하게 검증한 이름으로 current schema를 설정한다. PostgreSQL RTIMS를 별도 DB에 만들면 `RTIMS_POSTGRES_DATABASE_URL`, 같은 app DB에 만들면 기존 `DATABASE_URL`을 사용한다.
