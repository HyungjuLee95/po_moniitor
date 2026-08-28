# Messages MANUAL
최근 목록은 AaeMessageMonitor `getMessageLogs`, audit은 AdapterMessageMonitoring `getMessagesByIDs` 후 `getLogEntries`를 사용한다. SID와 message_id를 함께 식별자로 취급하고 payload는 기본 응답에서 제외한다.

Audit의 고정 wire 계약은 `getMessagesByIDs(messageIds=[id], referenceIds=['0'], correlationIds=['0'], archive=False)` 후 응답 `messageKey` 끝에 `\\`를 붙여 `getLogEntries(messageKey=..., archive=False, maxResults=100, olderThan=now, locale=None)`를 호출하는 것이다.

AAE 최근 목록의 `HOST_ID_TABLE/FIELD`는 서버의 Collector 설정에서 확인한 값만 사용한다. 빈 값으로 발생하는 DB object 오류를 임의 테이블명으로 우회하지 않는다. RTIMS가 설정되면 최근·실시간 목록의 우선 원본은 `MON_MSG_LOG`다.

RTIMS 조회의 상태 별칭은 `SUCCESS → S`, `FAILED → F`, `DELIVERING → P` 계열 코드도 함께 허용한다. `hours`는 최대 168시간이며 keyword는 송신·수신 서비스명에 대소문자 무관으로 적용한다.
