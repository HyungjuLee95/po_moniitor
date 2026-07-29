# Messages MANUAL
최근 목록은 AaeMessageMonitor `getMessageLogs`, audit은 AdapterMessageMonitoring `getMessagesByIDs` 후 `getLogEntries`를 사용한다. SID와 message_id를 함께 식별자로 취급하고 payload는 기본 응답에서 제외한다.

RTIMS 조회의 상태 별칭은 `SUCCESS → S`, `FAILED → F`, `DELIVERING → P` 계열 코드도 함께 허용한다. `hours`는 최대 168시간이며 keyword는 송신·수신 서비스명에 대소문자 무관으로 적용한다.
