# Dashboard API

`GET/PUT /api/v1/dashboard/preferences`는 로그인 사용자의 다음 설정을 조회·저장한다.

| 필드 | 계약 |
|---|---|
| `order`, `hidden`, `density` | 위젯 순서·숨김·밀도 |
| `favorite_views` | 사용자가 고정한 허용 View ID, 최대 8개 |
| `recent_views` | 최근 사용 View ID, 최대 8개 |
| `view_usage` | 허용 View ID별 누적 사용 횟수 |

권한은 `dashboard:read`/`dashboard:write`이며 PostgreSQL `iam.dashboard_preference.layout` JSONB가 원본이다.
