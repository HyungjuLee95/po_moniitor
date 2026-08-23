# Backend MANUAL

- router는 HTTP 계약과 권한 검사만 담당한다.
- service는 업무 로직, repository는 PostgreSQL, adapter는 SAP PO 호출을 담당한다.
- 모든 변경 API는 역할 permission을 검사하고 감사 이력을 남길 수 있어야 한다.
- PostgreSQL schema/table/column/index는 소문자 snake_case만 사용한다.
- migration은 `NNN_description.sql`로 추가한다.
- SAP 호출은 SID registry 검증 후 수행하며 credential과 base_url을 반환하지 않는다.
- 기존 RTIMS Oracle은 live 모니터링 원본으로 유지한다. PostgreSQL `rtims` schema는 로컬·오프라인 계약 검증용 호환 구조이며 runtime 원본 전환이나 자동 데이터 마이그레이션을 의미하지 않는다.
- RTIMS schema 생성은 `.env`의 `RTIMS_POSTGRES_DATABASE_URL`(미설정 시 `DATABASE_URL`), `RTIMS_ORACLE_*`, 별도 `RTIMS_ORACLE_DDL_*`만 읽는 `scripts/setup_rtims_databases.py`를 사용한다. Oracle owner와 runtime 계정이 다르면 `RTIMS_ORACLE_SCHEMA`를 owner로 지정해 current schema와 최소 object grant를 연결한다. 기존 객체를 변경·삭제하지 않으며 불완전한 기존 객체는 자동 보정하지 않고 검증 실패로 중단한다.
- 모든 도메인은 `API.md`에 REST 계약과 외부 SAP/Oracle 원본을 기록하며 내부 접속값은 기재하지 않는다.
- 도메인 테스트나 실연결 검증 오류는 해당 도메인의 `ERROR.md`, 공통 시작·DB·환경 오류는 영역 또는 루트 `ERROR.md`에 기록한다.
- Python 기준은 루트 `.python-version`, `backend/pyproject.toml`, CI와 contract test에서 모두 정확히 `3.11.7`로 유지한다. runtime·test 의존성을 변경하면 requirements와 pyproject metadata를 동시에 갱신한다.
