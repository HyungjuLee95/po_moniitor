# Channels ERROR
제어 실패는 permission, capability, SAP 계정 권한, adapter 응답을 차례로 확인한다.

## 2026-08-23 / 전체 채널 Query의 ComponentID 직렬화와 SAP 권한 차단

- 증상: `component_id=*` 전체 조회에서 `ComponentID=None`은 Zeep `ValidationError`, 문자열 `*`와 빈 문자열은 SAP Directory의 SOAP Fault가 발생했다.
- 영향: `/channels/inventory`와 이를 사용하는 대량 조회가 502로 종료됐다.
- 원인: 현재 WSDL은 `ComponentID`를 필수 element로 선언해 Python `None`을 직렬화하지 못했고, 실검증 계정에는 Directory Query 역할도 없었다.
- 해결: Legacy bulk 계약의 `None` 의미를 `xsd.SkipValue`로 변환해 element를 생략했다. 계정 권한은 코드에서 우회하지 않고 사내 역할 부여 확인 항목으로 분리했다.
- 검증: 단위 테스트에서 `PartyID=''`, 생략된 `ComponentID`, `ChannelID='*'` 계약을 확인했고, 실서버에서는 요청이 전송된 뒤 권한 SOAP Fault가 반환됨을 확인했다.
- 재발 방지: 전체 조회에 문자열 `*`를 `ComponentID`로 보내지 않으며, WSDL 로드 성공과 Directory operation 권한을 별도로 판정한다.
- 관련 파일: `backend/app/domains/channels/service.py`, `backend/tests/test_sap_po_integration.py`, `docs/internal-validation/SAP_PO_RUNTIME_VALIDATION_PROMPT.md`.

## 2026-08-27 / 권한 부여 후 CommunicationChannel Query 응답 파싱 누락

- 증상: SAP 계정 권한 부여 후 전체·단건 `CommunicationChannelIn.Query`는 SOAP Fault 없이 응답했지만 API 변환 결과가 0건이었다. 같은 채널의 `Read`는 27개 attribute를 반환했다.
- 영향: 시스템별 채널 정보, HRD 채널 검색과 Excel 대량 조회가 빈 목록으로 표시된다.
- 원인: 실응답 최상위 객체가 `CommunicationChannelID` 배열을 가지는데 공통 `records()`가 최상위 객체 자체를 record로 선택한다. 이후 `_channel_id()`는 배열을 ID 객체로 처리하지 못해 해당 행을 버린다.
- 해결: 미실시. 이번 작업은 계정 권한 실검증 범위이며 파서 수정은 별도 구현 작업으로 남겼다.
- 검증: 채널 상태 1,208건, 단건 `Read` 성공, Directory HTTP read 성공, ChannelAdmin `CHECK` 1건 성공과 함께 Query 실응답 shape를 확인했다.
- 재발 방지: Query fixture를 실제 `CommunicationChannelQueryOut -> CommunicationChannelID[]` 구조로 추가하고 전체·단건 변환 건수를 검증한다.
- 관련 파일: `backend/app/domains/channels/service.py`, `backend/app/integrations/sap_po/normalize.py`, `backend/tests/test_sap_po_integration.py`.
