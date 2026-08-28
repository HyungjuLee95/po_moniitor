# Auth SKILL

Verify that a fresh demo process authenticates only the configured admin account and rejects the removed built-in `operator` and `viewer` credentials.
인증 변경 시 단일 Administrator, 가입 직후 로그인 거부, 승인 후 로그인, ADMIN 추가 생성·승격 거부, 사용자별 허용 SID, 만료 토큰, 비활성 사용자를 검증한다. 토큰·가입 비밀번호·임시 비밀번호·hash를 로그에 남기지 않는다.
