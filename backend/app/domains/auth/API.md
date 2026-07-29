# Auth API

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/auth/login` | 공개 |
| GET | `/api/v1/auth/me` | 로그인 |
| POST | `/api/v1/auth/change-password` | 로그인 |
| POST | `/api/v1/auth/forgot-password` | 공개, 항상 동일 응답 |
| POST | `/api/v1/auth/reset-password` | 관리자 발급 1회 토큰 |
| GET/POST/PUT | `/api/v1/auth/users...` | `users:manage` |
| GET | `/api/v1/auth/password-reset-requests` | `users:manage` |
| POST | `/api/v1/auth/password-reset-requests/{id}/issue-token` | `users:manage` |

비밀번호 reset token은 ADMIN 응답에서 한 번만 제공하며 저장 시 SHA-256 hash만 보관한다.
