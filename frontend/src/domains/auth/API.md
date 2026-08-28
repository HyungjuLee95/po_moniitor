# Auth API

| 화면 | API |
|---|---|
| 로그인 | `POST /auth/login` |
| 가입 신청 | `POST /auth/register` |
| 비밀번호 찾기 요청 | `POST /auth/forgot-password` |
| 토큰 비밀번호 재설정 | `POST /auth/reset-password` |
| 내 비밀번호 변경 | `POST /auth/change-password` |
| 사용자·reset 요청 관리 | `/auth/users`, `/auth/password-reset-requests` |

`POST /auth/register`는 `{ username, display_name, password }`를 전송한다. 성공한 계정은 `VIEWER`, 비활성, 서버 범위 없음이며 Administrator 승인 전 로그인할 수 없다. 프론트는 가입자에게 역할·서버 선택을 제공하지 않는다.
