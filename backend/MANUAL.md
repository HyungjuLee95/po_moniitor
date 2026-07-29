# Backend MANUAL

- router는 HTTP 계약과 권한 검사만 담당한다.
- service는 업무 로직, repository는 PostgreSQL, adapter는 SAP PO 호출을 담당한다.
- 모든 변경 API는 역할 permission을 검사하고 감사 이력을 남길 수 있어야 한다.
- PostgreSQL schema/table/column/index는 소문자 snake_case만 사용한다.
- migration은 `NNN_description.sql`로 추가한다.
- SAP 호출은 SID registry 검증 후 수행하며 credential과 base_url을 반환하지 않는다.
- 기존 RTIMS Oracle은 모니터링 원본으로 유지하고 PostgreSQL과 혼합하거나 마이그레이션하지 않는다.
- 모든 도메인은 `API.md`에 REST 계약과 외부 SAP/Oracle 원본을 기록하며 내부 접속값은 기재하지 않는다.
- 도메인 테스트나 실연결 검증 오류는 해당 도메인의 `ERROR.md`, 공통 시작·DB·환경 오류는 영역 또는 루트 `ERROR.md`에 기록한다.
