# SAP PO Integration

공통 또는 서버별 Basic 인증 session, 서버별 endpoint·WSDL host alias override가 가능한 Zeep SOAP client, Directory HTTP API와 응답 정규화를 제공한다. 도메인은 이 계층을 직접 재구현하지 않고 `soap_client`, `call`, normalize helper를 사용한다. URL·credential·host alias는 frontend나 bootstrap에 반환하지 않는다.

지원 계약: Systatus, CommunicationChannelIn, ChannelAdmin, AaeMessageMonitor, AdapterMessageMonitoring, BusinessSystemIn, InterfaceMonitor, Directory `/dir/read/ext`, KeystoreHelp, KeystoreService.
