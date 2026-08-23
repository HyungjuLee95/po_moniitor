# RTIMS ERROR
연결 실패는 host·port·service·계정·방화벽·pool 상태를 확인한다. 실제 접속정보와 SQL bind 값을 오류 문서에 기록하지 않는다.

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
