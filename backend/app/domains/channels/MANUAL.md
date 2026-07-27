# Channels MANUAL
조회는 Systatus `getChannInfo`, inventory/detail은 CommunicationChannelIn `Query/Read`를 사용한다. 제어는 ChannelAdmin `setChannelAutomationStatus` 후 `startChannels/stopChannels`, `getChannelAutomationStatus` 검증 순서다. 비밀번호 포함 상세는 `channels:secrets` 권한이 필요하다.
