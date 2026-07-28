# Workspaces MANUAL

- 모든 레코드는 인증 사용자 소유로 저장하고 다른 사용자의 레코드를 반환하지 않는다.
- 단계는 `planned → in_progress → review → completed` 순서로만 진행한다.
- PostgreSQL 식별자는 소문자 snake_case를 사용한다.
- 삭제·수정·단계 진행은 `workspaces:write` 권한이 필요하다.
