# Channels API

| Method | Path | Permission | 원본 |
|---|---|---|---|
| GET | `/api/v1/channels` | `channels:read` | Systatus |
| GET | `/api/v1/channels/inventory` | `channels:read` | CommunicationChannelIn Query |
| GET | `/api/v1/channels/detail` | `channels:read` | CommunicationChannelIn Read |
| GET | `/api/v1/channels/detail-with-secret` | `channels:secrets` | Directory API |
| GET | `/api/v1/channels/statistics` | `channels:read` | RTIMS |
| GET | `/api/v1/channels/message-history` | `channels:read` | RTIMS |
| POST | `/api/v1/channels/control` | `channels:control` | ChannelAdmin |
| POST | `/api/v1/channels/batch-control-stream` | `channels:control` | ChannelAdmin SSE |
| GET | `/api/v1/channels/bulk-export` | `channels:secrets` | Channel/Directory XLSX |
| POST | `/api/v1/channels/bulk-preview` | `channels:secrets` | 업로드 XLSX와 SAP 비교 |

대량 Excel은 ADMIN 전용이며 응답에 `no-store`를 적용한다. 미리보기의 비밀번호 값은 마스킹한다. SSE 이벤트는 `progress`, `complete`, `error` 형식이다.
