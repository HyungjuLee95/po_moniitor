# Auth API

In demo mode, `POST /api/v1/auth/login` initially accepts only the configured `DEMO_ADMIN_USERNAME` and `DEMO_ADMIN_PASSWORD`. Other demo users exist only after self-registration and require Administrator approval.

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/auth/login` | 공개 |
| POST | `/api/v1/auth/register` | 공개 |
| GET | `/api/v1/auth/me` | 로그인 |
| POST | `/api/v1/auth/change-password` | 로그인 |
| POST | `/api/v1/auth/forgot-password` | 공개, 항상 동일 응답 |
| POST | `/api/v1/auth/reset-password` | 관리자 발급 1회 토큰 |
| GET/POST/PUT | `/api/v1/auth/users...` | `users:manage` |
| GET | `/api/v1/auth/password-reset-requests` | `users:manage` |
| POST | `/api/v1/auth/password-reset-requests/{id}/issue-token` | `users:manage` |

비밀번호 reset token은 ADMIN 응답에서 한 번만 제공하며 저장 시 SHA-256 hash만 보관한다.

## 공개 가입 계약

`POST /api/v1/auth/register`

```json
{
  "username": "lowercase.user",
  "display_name": "표시 이름",
  "password": "8자 이상 비밀번호"
}
```

성공은 HTTP 202와 `status=pending`, `role=VIEWER`를 반환한다. 저장 상태는 `active=false`, 서버 범위 없음이다. configured Administrator username과 중복 username은 HTTP 409, 잘못된 username 형식은 HTTP 422다. 추가 ADMIN 생성·승격과 Administrator 비활성·강등은 HTTP 409로 거부한다.
