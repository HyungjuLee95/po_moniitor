# Messages API

채널→메시지 목록은 `GET /channels/inventory`, `GET /channels/message-history`를 사용하고 선택 Message audit은 `GET /messages/{message_id}/audit?sid=`를 사용한다.

실시간 인터페이스는 `GET /messages?sid=&limit=&offset=&hours=&status=&keyword=`를 사용한다. `hours` 상한은 168시간이며 상태 별칭 `SUCCESS`, `FAILED`, `DELIVERING`을 지원한다.
