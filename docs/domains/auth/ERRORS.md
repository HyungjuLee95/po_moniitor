# Auth 오류

- 401: 토큰 누락·만료, 계정/비밀번호 불일치 확인
- 403: 사용자 역할과 endpoint 요구 permission 확인
- 운영 로그인 실패: `DEMO_MODE`, DB 연결, `active`, password hash 형식 확인
