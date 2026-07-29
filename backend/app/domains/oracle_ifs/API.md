# Oracle IFS API

| Method | Path | Permission | 원본 |
|---|---|---|---|
| GET | `/api/v1/oracle-ifs/interfaces` | `oracle-ifs:read` | PostgreSQL cache |
| POST | `/api/v1/oracle-ifs/sync` | `oracle-ifs:sync` | Oracle IFS → PostgreSQL |
| PUT | `/api/v1/oracle-ifs/target-date/{req_seq}` | `oracle-ifs:write` | PostgreSQL cache |

일반 사용자는 자신의 사용자 ID에 해당하는 cache만 조회하고 ADMIN은 전체를 조회한다.
