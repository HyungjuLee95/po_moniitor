# SAP PO Integration

공통 Basic 인증 session, Zeep SOAP client, Directory HTTP API와 응답 정규화를 제공한다. 도메인은 이 계층을 직접 재구현하지 않고 `soap_client`, `call`, normalize helper를 사용한다.

지원 계약: Systatus, CommunicationChannelIn, ChannelAdmin, AaeMessageMonitor, AdapterMessageMonitoring, BusinessSystemIn, Directory `/dir/read/ext`.
