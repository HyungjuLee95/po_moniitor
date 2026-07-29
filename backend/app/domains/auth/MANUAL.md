# Auth MANUAL

The local demo default is `admin / 1234`. This short password is for the isolated demo mode only. Production must use `DEMO_MODE=false` and PostgreSQL-backed users with the normal password policy.
데모 모드는 환경 계정을 사용하고 운영 모드는 `iam` schema를 조회한다. 비밀번호는 PBKDF2 hash만 저장한다. `ADMIN/admin`, `OPERATOR/관리자`, `VIEWER/일반` 역할을 사용하고 사용자별 `iam.user_server` 범위를 SID API에서 검사한다.

비밀번호 찾기는 사용자 존재 여부를 공개하지 않는다. 요청 후 ADMIN이 30분 유효 1회 토큰을 발급하고 사용자에게 내부 절차로 전달한다. DB에는 토큰 hash만 저장한다.
