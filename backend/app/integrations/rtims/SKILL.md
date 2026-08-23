# RTIMS SKILL
쿼리 변경 전 `rtims_sqlmap_analysis.md`의 table·status 의미를 확인한다. 대용량 조회에는 시간 범위·limit·offset을 강제하고 `select *` 신규 사용을 피한다.

Collector buffer(`MON_BUF_*`)와 운영 조회 원본(`MON_MSG_LOG`, 일별 통계, 오류 이력)을 혼동하지 않는다. 실제 schema 또는 상태 의미가 없으면 `docs/internal-validation/RTIMS_SCHEMA_VALIDATION_PROMPT.md`로 확인하고 결과 근거를 문서와 contract test에 반영한다.

Schema 변경은 `contract.py -> Oracle/PostgreSQL DDL -> schema_setup.py -> test_rtims_schema_setup.py` 순서로 동기화한다. 이미 존재하는 Oracle 테이블을 추정 `ALTER`하거나 DROP하지 않는다. 원본 DDL이 확인되면 새 순번 DDL/migration으로 보정하고 `ERROR.md`에 차이를 기록한다.
