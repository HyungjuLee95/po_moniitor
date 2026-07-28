# Channels MANUAL
조회는 Systatus `getChannInfo`, inventory/detail은 CommunicationChannelIn `Query/Read`를 사용한다. 제어는 ChannelAdmin `setChannelAutomationStatus` 후 `startChannels/stopChannels`, `getChannelAutomationStatus` 검증 순서다.

- `CHECK`: 상태만 다시 조회하며 변경하지 않는다.
- `START`/`STOP`: 제어 뒤 상태를 검증한다.
- `AUTOMATIC`/`MANUAL`/`EXTERNAL`: 각각 SCHEDULER/MANUAL/WEBSERVICE automation mode로 변환한다.
- 통계와 메시지 이력은 RTIMS `MON_MSG_LOG`, `MON_INTF_MAP`을 사용하며 사내 스키마에서 채널명 매핑과 latency 단위를 검증한다.
- 비밀번호 포함 상세는 `channels:secrets` 권한이 필요하고 목록·로그에 절대 노출하지 않는다.
