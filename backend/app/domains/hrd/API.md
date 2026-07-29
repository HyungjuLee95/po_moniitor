# HRD API

| Method | Path | Permission | Capability | 원본 |
|---|---|---|---|---|
| GET | `/api/v1/hrd/interfaces` | `hrd:read` | `hrd` | CommunicationChannelIn, 선택적 HANA |
| GET | `/api/v1/hrd/interfaces/excel` | `hrd:read` | `hrd` | 위 조회 결과 XLSX |
| POST | `/api/v1/hrd/test-message` | `hrd:test` | `hrd` | HttpAdapter servlet |

조회 필터는 `sid`, 선택적 `company_codes`, `table_names`, `search_ifid`다. 테스트 요청은 `sid`, `if_id`를 받으며 응답에는 HTTP 상태와 성공 여부만 포함하고 내부 URL·credential·XML 원문은 포함하지 않는다.
