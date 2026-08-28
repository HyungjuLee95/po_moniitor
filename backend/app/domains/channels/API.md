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

`statistics`와 `message-history`는 `hours`(기본 24, 1~168)를 받는다. RTIMS `MON_INTF_MAP`의 송·수신 인터페이스명에 `%channel_id%`를 적용하고 `MON_MSG_LOG.REQ_START_DTM` 시간창으로 제한한다.

CommunicationChannelIn `Query`는 `PartyID=''`, `ChannelID=channel_pattern`을 전송한다. 특정 시스템은 `ComponentID=component_id`, 전체 시스템을 뜻하는 `component_id=*`는 `ComponentID` element를 생략한다. `Read`는 `ReadContext='User'`와 `CommunicationChannelID[]`를 사용한다.
