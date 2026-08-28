# Messages ERROR
누락·중복은 조회 window, checkpoint, SID/message_id upsert 조건을 확인한다.

## 2026-08-23 / Adapter Audit 고정 파라미터 누락

- 증상: `getMessagesByIDs`에 message ID만 전달하고 `getLogEntries`에도 archive·locale과 messageKey suffix가 빠져 Legacy와 다른 SOAP 요청이 생성됐다.
- 영향: SAP 버전에 따라 Message ID를 찾지 못하거나 Audit 로그가 비어 보일 수 있었다.
- 원인: WSDL이 허용하는 최소 인자만 사용해 역분석 명세의 고정 호출 계약을 반영하지 않았다.
- 해결: reference/correlation placeholder, archive, messageKey `\\`, maxResults, olderThan, locale를 명세와 동일하게 전달했다.
- 검증: 계약 단위 테스트와 실서버의 최근 Message ID를 이용한 FastAPI Audit 조회에서 18개 로그 응답을 확인했다.
- 재발 방지: optional로 보이는 SOAP 인자도 역분석 golden contract에 고정돼 있으면 생략하지 않는다.
- 관련 파일: `backend/app/domains/messages/service.py`, `backend/tests/test_sap_po_integration.py`.

## 2026-08-23 / AAE 최근 목록의 Host ID 객체 설정 미확정

- 증상: 빈 `HOST_ID_TABLE/FIELD`로 `getMessageLogs`를 호출하면 SAP 측 DB object-not-found SOAP Fault가 발생했다.
- 영향: RTIMS를 사용하지 않는 AAE 최근 메시지 fallback은 현재 임시 서버에서 동작을 확정할 수 없다.
- 원인: 제공 자료에는 파라미터 이름과 `global.useHostId` 분기만 있고 서버별 실제 값이 없다.
- 해결: 임의 객체명을 추정하지 않고 사내 Collector 설정 확인 항목으로 남겼다. 독립적인 `getMessageLog2Sync`와 Adapter Audit은 정상임을 별도 확인했다.
- 검증: 동일 계정으로 WSDL 파싱, 동기 메시지 4건, Audit 18건은 성공했고 `getMessageLogs`만 DB object Fault가 재현됐다.
- 재발 방지: 서버별 Collector의 `global.useHostId`, `HOST_ID_TABLE`, `HOST_ID_FIELD`, `DELIVERY_SEMANTICS`를 확인한 뒤 설정한다.
- 관련 문서: `docs/internal-validation/SAP_PO_RUNTIME_VALIDATION_PROMPT.md`.

## 2026-08-27 / 권한 부여 후 메시지 API 재검증

- 증상: 전체 SAP 권한을 부여한 뒤에도 `getMessageLogs`만 `ORA-00942 / DB_OBJECT_UNKNOWN`으로 실패했다.
- 영향: RTIMS를 사용하지 않는 `/messages` AAE fallback은 HTTP 502를 반환한다.
- 원인: SAP 권한이 아니라 서버별 `HOST_ID_TABLE/HOST_ID_FIELD` 또는 해당 DB 객체 계약이 아직 확정되지 않았다.
- 해결: 미실시. 임의 테이블명을 넣지 않고 Collector 원본 설정 확인을 유지한다.
- 검증: 같은 계정과 서버에서 `getMessageLog2Sync` 최근 Message ID 7건과 그중 1건의 Adapter Audit 로그 18건을 정상 조회했다. 따라서 Adapter Audit 권한은 정상이다.
- 재발 방지: `getMessageLogs` 실패를 계정 권한 오류로 분류하지 않고 Oracle 오류 코드와 Collector 파라미터를 함께 확인한다.
- 관련 문서: `docs/internal-validation/SAP_PO_RUNTIME_VALIDATION_PROMPT.md`.
