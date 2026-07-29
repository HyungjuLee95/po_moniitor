# Messages API

`GET /api/v1/messages?sid=&limit=&offset=&hours=&status=&keyword=`는 RTIMS 또는 AaeMessageMonitor 최근 메시지를 반환한다.

- `limit`: 1~1000
- `offset`: 0 이상
- `hours`: 1~168
- `status`: 원본 상태 또는 `SUCCESS/FAILED/DELIVERING`
- `keyword`: 인터페이스·송신·수신 시스템 검색

`GET /api/v1/messages/{message_id}/audit?sid=`는 AdapterMessageMonitoring audit을 반환한다. 모두 `messages:read`가 필요하며 payload 원문은 반환하지 않는다.
