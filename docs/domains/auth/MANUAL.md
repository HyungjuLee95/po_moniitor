# Auth 도메인 매뉴얼

로그인, JWT 발급, 현재 사용자와 역할 확인을 담당한다. `POST /api/v1/auth/login`은 form 형식의 username/password를 받고, `GET /api/v1/auth/me`는 Bearer 토큰을 검증한다. 운영 모드에서는 PostgreSQL `iam` schema를 사용한다.
