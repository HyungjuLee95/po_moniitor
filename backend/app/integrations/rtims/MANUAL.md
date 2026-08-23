# RTIMS MANUAL
연결값은 `RTIMS_ORACLE_*` 환경 변수로 관리한다. pool은 lazy 생성하고 SQL은 bind parameter만 사용한다. 기존 table/column 이름은 Oracle 원본을 유지하고 API DTO에서 소문자로 변환한다.

## Schema 생성·검증

- PostgreSQL 대상은 `RTIMS_POSTGRES_DATABASE_URL`(비어 있으면 `DATABASE_URL`), Oracle 대상은 `RTIMS_ORACLE_HOST/PORT/SERVICE`와 별도 `RTIMS_ORACLE_DDL_USER/PASSWORD`를 사용한다.
- runtime `RTIMS_ORACLE_USER/PASSWORD`에는 원칙적으로 DDL 권한을 주지 않는다.
- DDL owner와 runtime 사용자가 다르면 `RTIMS_ORACLE_SCHEMA=<DDL owner>`가 필수다. 설치기는 runtime 사용자에게 14개 테이블 `SELECT`와 `MON_ERR_HIST(ERR_STATE, ERR_PROC_MSG, USER_ID)` `UPDATE`만 grant하고, backend pool은 해당 owner를 current schema로 사용한다.
- `.\scripts\setup-rtims-databases.ps1 -Target all`은 누락 객체 생성 후 테이블·필수 컬럼을 검증한다.
- `-CheckOnly`는 DDL을 실행하지 않는다. 기존 Oracle schema에는 이 모드부터 사용한다.
- 두 DB는 분산 transaction이 아니므로 `all` 실행 중 두 번째 DB가 실패하면 첫 번째 DB의 생성은 유지된다. DDL이 멱등이므로 원인 해결 후 재실행한다.
- PostgreSQL은 `rtims` schema와 소문자 `snake_case`, Oracle은 legacy 대문자 이름을 사용한다.
- 기존 테이블이 있으나 필수 컬럼이 빠진 경우 자동 `ALTER`하지 않고 실패한다. DBA가 원본 DDL과 영향도를 확인한 뒤 별도 migration을 승인해야 한다.

화면별 원본은 다음과 같다.

- 최근·실시간 메시지와 건수: `MON_MSG_LOG LEFT JOIN MON_INTF_MAP`
- 채널 통계·메시지 이력: `MON_MSG_LOG`, `MON_INTF_MAP`, 채널명 `%LIKE%`, 명시적 시간창
- CPU·Memory: `MON_RES_USAGE`, `MON_RESOURCE`, Oracle 수집일자와 `MINUTE_DAY`
- Adapter Engine Queue: `MON_AE_QUEUE`; Integration Engine 대기: `MON_Q_STATUS`
- 장애 조회·해결: `MON_ERR_HIST`와 인터페이스·그룹·오류코드 조인
- 시스템 그룹 통계: `MON_DAILY_STATISTICS`, `MON_DAILY_CLOSE_STAT`, `PM_INTERFACE`, `PM_INTF_GROUP`

시간 범위·SID·상태·검색어는 bind parameter로 전달한다. 리소스 상태는 사용률 `>90 Red`, `>70 Yellow`, 나머지 `Green`이다. Oracle에서 조회한 timestamp는 API 직렬화 시 ISO 문자열로 변환한다.

`MON_DAILY_CLOSE_STAT`의 정확한 DDL, RTIMS 상태코드와 Collector freshness는 사내 확인 전까지 미검증 계약이다. 제공 자료에 없는 해당 객체는 `INTF_MAP_ID`, `YMDD`, `HOUR`, `COUNT`만 가진 최소 호환 테이블로 생성한다. 확인 질문은 `docs/internal-validation/RTIMS_SCHEMA_VALIDATION_PROMPT.md`를 사용한다.
