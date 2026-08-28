# RTIMS ERROR
연결 실패는 host·port·service·계정·방화벽·pool 상태를 확인한다. 실제 접속정보와 SQL bind 값을 오류 문서에 기록하지 않는다.

## 2026-08-23 / 로컬 VPN에서 RTIMS Oracle 포트 타임아웃

- 증상: 기존 `.env` RTIMS 설정은 완전한 것으로 판정됐지만 DNS 해석 후 TCP 연결과 Oracle thin 연결이 타임아웃됐다.
- 영향: RTIMS contract 및 `/messages`·대시보드의 실제 Oracle 조회는 이번 로컬 검증에서 실행하지 못했다.
- 원인: 현재 VPN 경로에서 대상 Oracle listener 포트까지 통신되지 않는다. 계정·service 유효성은 TCP 이전 단계에서 확인할 수 없다.
- 해결: 코드나 접속값을 추정 변경하지 않고 네트워크·방화벽 확인 항목으로 분리했다.
- 검증: DNS 해석 성공, TCP timeout, Oracle driver `OperationalError`를 민감정보 없이 구분했다.
- 재발 방지: RTIMS smoke test는 DNS → TCP → listener/service → 계정 → schema contract 순서로 수행한다.
- 관련 문서: `docs/internal-validation/RTIMS_SCHEMA_VALIDATION_PROMPT.md`.

## 2026-08-23 / MON_DAILY_CLOSE_STAT 원본 DDL 부재

- 증상: 시스템 그룹 통계 SQL은 `MON_DAILY_CLOSE_STAT.INTF_MAP_ID/YMDD/HOUR/COUNT`를 사용하지만 제공 명세에 해당 테이블 DDL이 없었다.
- 영향: 신규 Oracle·PostgreSQL schema를 원본과 완전히 동일하다고 보장할 수 없고, Collector 적재 SQL이 추가 컬럼·키를 요구할 수 있다.
- 원인: 역분석 자료에는 조회 SQL 경로만 있고 원본 schema export가 포함되지 않았다.
- 해결: 현재 reachable backend가 사용하는 네 컬럼의 최소 호환 테이블만 생성하고 DDL 주석·문서·사내 검증 프롬프트에 provisional 상태를 표시했다.
- 검증: DDL contract test가 14개 객체와 repository 필수 컬럼 포함 여부를 검사한다. 실제 Oracle Collector 적재 검증은 남아 있다.
- 재발 방지: 원본 DDL 확인 전 자동 `ALTER`와 전체 RTIMS 호환 표기를 금지하고, 확인 후 새 순번 migration으로 교정한다.
- 관련 파일: `backend/oracle/001_rtims_monitoring_schema.sql`, `backend/migrations/006_rtims_compatibility.sql`, `docs/internal-validation/RTIMS_SCHEMA_VALIDATION_PROMPT.md`.

## 2026-08-23 / 구형 Collector buffer와 live RTIMS 조회 테이블 혼용

- 증상: 최근 메시지는 `MON_BUF_AAE_MSG`, 장애는 `MON_INCI_LOG`를 조회해 실제 RTIMS 화면과 결과가 다르거나 테이블 오류가 발생할 수 있었다.
- 영향: 실시간 인터페이스, 채널 이력과 장애 관리 화면이 Collector 처리 전 buffer 또는 존재하지 않는 객체를 원본으로 사용할 수 있었다.
- 원인: dead 구형 서비스 SQL과 reachable RTIMS 전용 서비스 SQL을 구분하지 못한 뼈대 구현이었다.
- 해결: 최근 메시지를 `MON_MSG_LOG`/`MON_INTF_MAP`, 장애를 `MON_ERR_HIST` 5개 조인과 해결 UPDATE 계약으로 교정하고 리소스·채널 시간창 binding을 반영했다.
- 검증: Oracle 없는 contract test를 추가하고 compileall·문서 검증을 수행했다. 실제 Oracle smoke test는 사내 환경에서 남아 있다.
- 재발 방지: SQL-007~018 live 매핑과 사내 schema 검증 프롬프트를 변경 기준으로 사용한다.
- 관련 파일: `backend/app/integrations/rtims/repository.py`, `backend/tests/test_rtims_contract.py`.

## 2026-08-28 / 조회 호환 DDL만으로 Collector 실행 불가

- 증상: `setup-rtims-databases`로 생성한 Oracle schema에 Collector를 켜면 buffer·sequence·procedure 객체 부족으로 실패할 수 있다.
- 영향: 조회 API 14개 객체 검증 성공을 전체 Legacy Collector schema 호환 성공으로 오인할 수 있다.
- 원인: 기존 원클릭 DDL은 화면 조회 계약을 위해 만든 최소 schema이며 `MON_BUF_AAE_MSG`와 `process_msg_logs` 의존 전체 객체를 포함하지 않는다.
- 해결: Collector 시작 전 필요한 객체·sequence·procedure와 별도 최소 권한을 문서화하고 기존 전체 RTIMS schema 또는 DBA 검증 원본 DDL을 전제한다.
- 검증: Oracle 없이 정확한 buffer DML·procedure 이름·checkpoint transaction을 계약 테스트했다. 실제 Oracle compile·실행 검증은 사내 DBA 확인 대상으로 남긴다.
- 재발 방지: 조회 schema 검증과 Collector write schema 검증을 별도 완료 조건으로 표시한다.

## 2026-08-28 / 전체 Legacy DDL의 View 선행 의존성

- 증상: 새 Oracle schema에 번호 순서대로 DDL을 적용하면 `oracle_create_03_mon.sql`의 `V_MON_MSG_PAYLOAD` 생성에서 `GET_TRG_SYSTEM invalid identifier`로 중단됐다.
- 영향: 03 파일 앞부분의 Collector table은 생성되지만 View 이후 전체 설치가 실패한 것으로 처리된다.
- 원인: View가 참조하는 `get_src_system/get_trg_system` 함수는 다음 `oracle_create_04_col.sql` 후반에 정의되어 있다.
- 해결: 일회용 schema에서는 03의 table을 생성한 뒤 04의 함수를 포함한 Collector procedure를 생성하고 마지막에 View를 다시 생성했다.
- 검증: `PROCESS_AAE_MSGS`, `PROCESS_MSG_LOGS`, `GET_INTF_MAP_ID`, `REGISTER_INTERFACE`, `V_MON_MSG_PAYLOAD`가 모두 VALID이며 실제 합성 메시지가 처리됐다.
- 재발 방지: 전체 DDL 패키지를 제품에 포함할 때 함수와 View를 별도 순번 파일로 분리하고 compile error를 설치 실패로 처리한다.

## 2026-08-28 / Governance DDL의 외부 schema 의존성

- 증상: `oracle_create_06_gvn.sql`의 `INTERFACE_GVN_INTF_MASTERS`가 compile error로 INVALID 상태가 됐다.
- 영향: governance master 동기화는 실행할 수 없지만 RTIMS Collector core procedure 실행에는 영향이 없다.
- 원인: 프로시저가 `HYNIXRTIMS.*`, `GEAIAPP.IFS_DEF_INFO`, `GEAIAPP.SYS_MST_INFO`를 직접 참조하며 일회용 schema에는 해당 owner·table·grant가 없다.
- 해결: 로컬 Collector 검증에서는 06을 선택 연동으로 분리하고 core object validity와 실제 message pipeline만 판정했다.
- 검증: INVALID object는 `INTERFACE_GVN_INTF_MASTERS` 한 건이며 Collector success·checkpoint·rollback smoke test는 통과했다.
- 재발 방지: 사내 적용 전 실제 owner 이름·synonym·grant를 확인하고 governance 기능을 별도 capability로 활성화한다.

## 2026-08-28 / 원본 Collector testdata의 평문 연결정보와 자동 활성화

- 증상: `oracle_testdata_02_collector.sql`에 주소·사용자·비밀번호와 `MON_COLLECTOR_INSTANCE.ACTIVE='Y'`가 포함되어 있었다.
- 영향: 공유 또는 운영성 RTIMS에 실행하면 평문 비밀값이 저장되고 기존 scheduler가 외부 시스템 호출을 시작할 수 있다.
- 원인: 원본 파일은 특정 과거 개발환경을 그대로 복원하는 seed다.
- 해결: 원본 02 파일은 실행하지 않고 loopback 전용 합성 데이터와 Python smoke script를 사용했다.
- 검증: Docker port는 loopback에만 공개했고 외부 RTIMS에는 접속하지 않았다.
- 재발 방지: 전달받은 seed는 실행 전에 connection·credential·ACTIVE·COMMIT 문을 검사하고 local-safe fixture로 변환한다.
