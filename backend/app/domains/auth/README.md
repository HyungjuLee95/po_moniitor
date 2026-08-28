# Auth

`DEMO_MODE=true` starts with one built-in Administrator account only: `admin` with the password configured by `DEMO_ADMIN_PASSWORD`. Other users self-register and remain inactive until approval. Demo registrations are in-memory and reset with the backend process.
로그인, JWT 발급, 공개 가입, 사용자 활성화·역할·접근 서버, 사용자 직접 변경과 Administrator 승인형 비밀번호 찾기를 담당한다. 추가 ADMIN 생성·승격은 허용하지 않으며 전체 계약은 `API.md`를 따른다.
