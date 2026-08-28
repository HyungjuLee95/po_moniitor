# RTIMS MANUAL
연결값은 `RTIMS_ORACLE_*` 환경 변수로 관리한다. 조회·장애처리 runtime 계정과 Collector DML 계정은 `RTIMS_COLLECTOR_ORACLE_USER/PASSWORD`로 분리할 수 있으며 비어 있으면 runtime 계정을 사용한다. pool은 lazy 생성하고 SQL 값은 bind parameter만 사용한다. 기존 table/column 이름은 Oracle 원본을 유지하고 API DTO에서 소문자로 변환한다.

## Schema 생성·검증

- PostgreSQL 대상은 `RTIMS_POSTGRES_DATABASE_URL`(비어 있으면 `DATABASE_URL`), Oracle 대상은 `RTIMS_ORACLE_HOST/PORT/SERVICE`와 별도 `RTIMS_ORACLE_DDL_USER/PASSWORD`를 사용한다.
- runtime `RTIMS_ORACLE_USER/PASSWORD`에는 원칙적으로 DDL 권한을 주지 않는다.
- DDL owner와 runtime 사용자가 다르면 `RTIMS_ORACLE_SCHEMA=<DDL owner>`가 필수다. 설치기는 runtime 사용자에게 14개 테이블 `SELECT`와 `MON_ERR_HIST(ERR_STATE, ERR_PROC_MSG, USER_ID)` `UPDATE`만 grant하고, backend pool은 해당 owner를 current schema로 사용한다.
- `.\scripts\setup-rtims-databases.ps1 -Target all`은 누락 객체 생성 후 테이블·필수 컬럼을 검증한다.
- `-CheckOnly`는 DDL을 실행하지 않는다. 기존 Oracle schema에는 이 모드부터 사용한다.
- 두 DB는 분산 transaction이 아니므로 `all` 실행 중 두 번째 DB가 실패하면 첫 번째 DB의 생성은 유지된다. DDL이 멱등이므로 원인 해결 후 재실행한다.
- PostgreSQL은 `rtims` schema와 소문자 `snake_case`, Oracle은 legacy 대문자 이름을 사용한다.
- 기존 테이블이 있으나 필수 컬럼이 빠진 경우 자동 `ALTER`하지 않고 실패한다. DBA가 원본 DDL과 영향도를 확인한 뒤 별도 migration을 승인해야 한다.

## Collector Oracle 계약

- 현재 원클릭 Oracle DDL은 조회 화면용 14개 객체만 생성하므로 Collector를 새 schema에서 바로 켤 수 없다.
- Collector에는 `MON_BUF_AAE_MSG`, `MON_AAE_SEQ_ID`, `MON_COLLECTOR_PARAMS`, `MON_COLLECTOR_LOG`, `MON_COL_LOG_ID`, `process_msg_logs`와 해당 프로시저가 참조하는 전체 RTIMS 객체가 필요하다.
- 별도 Collector 계정의 최소 권한은 owner 구성에 따라 `MON_BUF_AAE_MSG INSERT`, `MON_COLLECTOR_PARAMS SELECT/INSERT/UPDATE`, `MON_COLLECTOR_LOG SELECT/INSERT`, 두 sequence SELECT, `process_msg_logs EXECUTE`다. 프로시저가 invoker rights이거나 다른 owner 객체를 참조하면 DBA가 본문 기준 추가 권한을 산정한다.
- `oracle_instance_id`는 서버·profile 전체에서 유일해야 하며 `MON_COLLECTOR_PARAMS.INSTANCE_ID`와 `MON_COLLECTOR_LOG.INSTANCE_ID`에 그대로 사용된다.
- 시간은 HANA UTC 문자열을 기존 mapper와 같은 형식으로 Oracle `Asia/Seoul` timestamp에 변환한다.
- buffer·procedure·checkpoint·성공 로그 중 하나라도 실패하면 rollback한다. 오류 로그는 rollback 후 별도 transaction으로 기록을 시도한다.
- 현재 in-process lock만 제공하므로 scheduler를 실행하는 backend는 한 인스턴스로 제한한다.

## 일회용 로컬 Oracle smoke test

`scripts/smoke_test_rtims_collector_oracle.py`는 loopback host만 허용한다. 전체 Legacy RTIMS DDL이 적용된 폐기 가능한 Oracle schema에 합성 BE 메시지와 전용 `TST/900001` 기준정보를 넣고 다음을 실제로 검증한다.

- Python repository의 `MON_BUF_AAE_MSG` insert
- `process_msg_logs`와 `MON_MSG_LOG` 가공 결과
- Oracle `TIMESTAMP/MESSAGE_ID` checkpoint와 성공 로그
- 상태 API용 Oracle projection
- 잘못된 buffer row의 transaction rollback

```powershell
$env:RTIMS_TEST_ORACLE_HOST="127.0.0.1"
$env:RTIMS_TEST_ORACLE_PORT="15211"
$env:RTIMS_TEST_ORACLE_SERVICE="FREEPDB1"
$env:RTIMS_TEST_ORACLE_USER="RTIMS_TEST"
$env:RTIMS_TEST_ORACLE_PASSWORD="<local-disposable-password>"
py -3.11 scripts\smoke_test_rtims_collector_oracle.py
Remove-Item Env:RTIMS_TEST_ORACLE_PASSWORD
```

스크립트는 기존 `.env`의 RTIMS 주소를 사용하지 않으며 loopback이 아니면 실행을 거부한다. 원본 `oracle_testdata_02_collector.sql`은 평문 접속정보와 활성 Collector instance가 있으므로 직접 실행하지 않는다.

제공된 전체 DDL의 `V_MON_MSG_PAYLOAD`는 뒤 파일의 `get_src_system/get_trg_system` 함수에 선행 의존한다. 새 schema에서는 함수가 생성된 뒤 View를 생성해야 한다. `oracle_create_06_gvn.sql`은 별도 `HYNIXRTIMS`·`GEAIAPP` schema를 전제로 하는 선택적 governance 연동이며 RTIMS Collector core smoke test 완료 조건에서 제외한다.

화면별 원본은 다음과 같다.

- 최근·실시간 메시지와 건수: `MON_MSG_LOG LEFT JOIN MON_INTF_MAP`
- 채널 통계·메시지 이력: `MON_MSG_LOG`, `MON_INTF_MAP`, 채널명 `%LIKE%`, 명시적 시간창
- CPU·Memory: `MON_RES_USAGE`, `MON_RESOURCE`, Oracle 수집일자와 `MINUTE_DAY`
- Adapter Engine Queue: `MON_AE_QUEUE`; Integration Engine 대기: `MON_Q_STATUS`
- 장애 조회·해결: `MON_ERR_HIST`와 인터페이스·그룹·오류코드 조인
- 시스템 그룹 통계: `MON_DAILY_STATISTICS`, `MON_DAILY_CLOSE_STAT`, `PM_INTERFACE`, `PM_INTF_GROUP`

시간 범위·SID·상태·검색어는 bind parameter로 전달한다. 리소스 상태는 사용률 `>90 Red`, `>70 Yellow`, 나머지 `Green`이다. Oracle에서 조회한 timestamp는 API 직렬화 시 ISO 문자열로 변환한다.

`MON_DAILY_CLOSE_STAT`의 정확한 DDL, RTIMS 상태코드, Collector procedure의 전체 의존 객체와 HANA 운영 인덱스는 사내 확인 전까지 미검증 계약이다. 제공 자료에 없는 해당 객체는 `INTF_MAP_ID`, `YMDD`, `HOUR`, `COUNT`만 가진 최소 호환 테이블로 생성한다. 확인 질문은 `docs/internal-validation/RTIMS_SCHEMA_VALIDATION_PROMPT.md`와 Collector follow-up 문서를 사용한다.
