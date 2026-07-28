# Auth MANUAL
데모 모드는 환경 계정을 사용하고 운영 모드는 `iam` schema를 조회한다. 비밀번호는 PBKDF2 hash만 저장한다. `ADMIN/admin`, `OPERATOR/관리자`, `VIEWER/일반` 역할을 사용하고 사용자별 `iam.user_server` 범위를 SID API에서 검사한다.
