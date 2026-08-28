# Interfaces ERROR
중복·검색 누락은 namespace, sender/receiver, 대소문자·공백 정규화를 확인한다.

## 2026-08-23 / 실제 WSDL operation·응답 필드 불일치

- 증상: Business System은 WSDL에 없는 `getBusinessSystemList`를 호출해 `AttributeError`가 발생했고, InterfaceMonitor는 실제 `getAllInterfaces`를 호출 후보에서 제외해 실패했다. operation을 직접 호출해도 기존 parser는 974건을 0건으로 변환했다.
- 영향: 시스템별 채널 정보의 첫 단계와 Namespace 인벤토리를 사용할 수 없었다.
- 원인: 명세의 논리 기능명을 SOAP operation명으로 오인했고, 실제 응답의 `fromAction/fromActionNamespace/fromService/toAction/toActionNamespace/toService` 계약이 parser에 없었다.
- 해결: BusinessSystemIn `Query` 계약과 `ComponentID` 추출을 적용하고, InterfaceMonitor `getAllInterfaces()` 및 실제 필드 매핑을 추가했다.
- 검증: 계약 단위 테스트 통과, 실서버 `getAllInterfaces()`와 FastAPI `/interfaces/namespaces`가 974건을 반환했다. BusinessSystem Query는 실검증 계정의 SAP Directory 조회 역할 부재로 502까지 확인했다.
- 재발 방지: operation 이름은 WSDL의 binding 목록으로 확정하고, smoke test에서 raw count와 변환 count를 함께 비교한다.
- 관련 파일: `backend/app/domains/interfaces/service.py`, `backend/tests/test_sap_po_integration.py`.

## 2026-08-23 / BusinessSystem Query 계정 권한 부족

- 증상: 올바른 `Query(BusinessSystemID=None, Description=None, AdministrativeData=None)` 요청이 SAP 서버에서 insufficient-authorization SOAP Fault로 거부됐다.
- 영향: `/interfaces`와 시스템 선택 기반 채널 조회가 현재 임시 계정으로는 502를 반환한다.
- 원인: 실검증 계정에 SAP Directory API 조회 역할이 부여되지 않았다.
- 해결: 권한을 추정하거나 우회하지 않고 필요한 역할 확인을 사내 검증 항목으로 남겼다.
- 검증: WSDL 인증·파싱은 성공하지만 실제 Query에서만 권한 Fault가 재현됐다.
- 재발 방지: 서버 계정 인수 시 WSDL 접근과 BusinessSystem/CommunicationChannel Query 권한을 별도 체크한다.
- 관련 문서: `docs/internal-validation/SAP_PO_RUNTIME_VALIDATION_PROMPT.md`.

## 2026-08-27 / SAP 계정 권한 부여 후 Directory 조회 재검증

- 증상: 이전에는 `BusinessSystemIn.Query`가 insufficient-authorization Fault로 거부됐다.
- 영향: 시스템 선택 기반 채널 조회를 시작할 수 없었다.
- 원인: 기존 검증 계정의 SAP Directory 조회 역할 부족이었다.
- 해결: SAP 계정에 승인된 조회·모니터링 역할을 부여했다.
- 검증: 실제 `BusinessSystemIn.Query` 124건, `InterfaceMonitor.getAllInterfaces()` 변환 987건을 확인했다.
- 재발 방지: 계정 인수 smoke test에서 WSDL 200과 실제 Query 실행을 별도 검사한다.
- 관련 파일: `backend/app/domains/interfaces/service.py`, `docs/internal-validation/SAP_PO_RUNTIME_VALIDATION_PROMPT.md`.
