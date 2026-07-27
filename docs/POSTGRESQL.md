# PostgreSQL 규칙

PostgreSQL은 따옴표 없는 식별자를 소문자로 해석하므로 모든 schema, table, column을 처음부터 소문자 snake_case로 작성합니다. `"CamelCase"` 같은 따옴표 식별자는 금지합니다.

- schema로 책임을 분리한다: `iam`, `configuration`, `monitoring`, `integration`
- PK는 `<entity>_id`, FK는 참조 대상의 PK 이름을 사용한다.
- 시간은 `timestamptz`, 구조가 유동적인 부가정보만 `jsonb`를 사용한다.
- 상태·환경 값에는 check constraint를 둔다.
- 조회 조건과 정렬에 맞춰 복합 인덱스를 설계한다.
- 마이그레이션은 수정하지 않고 새 순번 파일로 추가한다.
- SAP 원본 이력과 사용자 조작 이력을 구분해 보존한다.

최초 스키마는 `backend/migrations/001_initial.sql`입니다.
