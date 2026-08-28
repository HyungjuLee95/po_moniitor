# SAP PO 런타임 설정 확인 프롬프트

아래 프롬프트를 사내 LLM에 그대로 전달한다. 계정명·비밀번호·실제 host/IP·메시지 payload는 답변에 포함하지 않는다.

```text
SAP PO와 기존 RTIMS Collector 소스/설정을 근거로 다음 항목을 확인해 주세요. 추정하지 말고 파일 경로, 클래스/메서드, 설정 key 또는 역할 정의를 근거로 답변해 주세요. 비밀번호, 실제 사용자명, 실제 host/IP, payload 원문은 마스킹하세요.

1. BusinessSystemInService.Query와 CommunicationChannelInService.Query/Read를 실행하는 기술 계정에 필요한 SAP Java 역할을 정확히 나열해 주세요.
   - WSDL 조회 권한과 실제 Query/Read 실행 권한을 구분해 주세요.
   - DISPLAY 역할만으로 충분한지, DEVELOP 역할도 필요한지 확인해 주세요.

2. PO 서버/SID별 AaeMessageMonitor getMessageLogs 설정을 표로 정리해 주세요.
   - SERVER_ID 또는 SID
   - DELIVERY_SEMANTICS
   - global.useHostId
   - HOST_ID_TABLE
   - HOST_ID_FIELD
   - 값의 출처(MON_COLLECTOR_CONN, MON_COLLECTOR_PARAMS, properties 또는 코드)
   - useHostId=false일 때 SOAP 인자에 실제로 전달되는 값(빈 문자열, 공백, 특정 placeholder 등)

3. getMessageLogs 호출 직전에 위 값을 만드는 원본 코드와 최종 호출 코드를 찾아 파라미터 순서·타입을 확인해 주세요.
   getMessageLogs(timestamp, deliverySemantics, hostIdTable, hostIdField, limitCount)

4. InterfaceMonitorService.getAllInterfaces 응답 DTO의 각 필드 의미를 확인해 주세요.
   - fromAction/fromActionNamespace/fromService
   - toAction/toActionNamespace/toService
   - objectId/sequence
   특히 화면의 interface_name, namespace, direction, source_system, target_system, operation에 어떤 필드를 매핑해야 하는지 근거와 함께 제시해 주세요.

5. 결과 끝에 다음 세 분류로 정리해 주세요.
   - CONFIRMED: 코드/설정 근거가 있는 값
   - ENVIRONMENT-SPECIFIC: SID마다 달라 .env에 넣어야 하는 값
   - UNKNOWN: 추가 파일 또는 관리자 확인이 필요한 값
```
