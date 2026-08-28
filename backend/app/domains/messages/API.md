# Messages API

`GET /api/v1/messages?sid=&limit=&offset=&hours=&status=&keyword=`는 RTIMS 또는 AaeMessageMonitor 최근 메시지를 반환한다.

- `limit`: 1~1000
- `offset`: 0 이상
- `hours`: 1~168
- `status`: 원본 상태 또는 `SUCCESS/FAILED/DELIVERING`
- `keyword`: 인터페이스·송신·수신 시스템 검색

RTIMS가 설정된 경우 원본은 `MON_MSG_LOG LEFT JOIN MON_INTF_MAP`이며 `meta.total`은 동일한 시간·상태·검색 조건의 SQL-010 count다. `GET /api/v1/messages/count?sid=&hours=&status=&keyword=`도 동일 count를 `{data:{count}}`로 반환한다.

`GET /api/v1/messages/{message_id}/audit?sid=`는 AdapterMessageMonitoring audit을 반환한다. 모두 `messages:read`가 필요하며 payload 원문은 반환하지 않는다.

Audit 외부 호출 계약은 `getMessagesByIDs(messageIds=[message_id], referenceIds=['0'], correlationIds=['0'], archive=False)` → 각 `messageKey`의 `getLogEntries(archive=False, maxResults=100, olderThan=현재시각, locale=None)`다.
