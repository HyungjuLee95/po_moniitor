# SAP PO Integration ERROR

연결 실패는 SID 설정, DNS, 포트, 계정, TLS, WSDL path, operation signature 순으로 확인한다. 해결 기록에 실제 URL·사용자·비밀번호·payload를 복사하지 않는다.

## 2026-08-23 / WSDL 내부 short hostname DNS 실패

- 증상: WSDL URL 자체는 인증 포함 HTTP 200이지만 일부 계약을 Zeep으로 읽을 때 내부 import hostname의 name resolution 오류가 발생했다.
- 영향: 채널 제어와 AdapterMessageMonitoring client만 초기화되지 않아 대응 API가 호출 전에 실패했다.
- 원인: SAP PO가 외부에서 접근하는 FQDN과 다른 short hostname을 WSDL import·binding address에 발행했고 VPN DNS가 그 이름을 해석하지 못했다.
- 해결: `PoServer.host_aliases`에 명시된 hostname만 해당 서버 origin으로 치환하는 session을 추가했다.
- 검증: alias 미설정·설정 URL 변환 단위 테스트와 임시 서버의 7개 WSDL 재파싱 및 read-only operation smoke test를 수행했다.
- 재발 방지: 시스템 hosts 파일에 의존하지 않고 서버별 alias를 `.env`에서 명시하며, 외부 host는 절대 자동 치환하지 않는다.
- 관련 파일: `backend/app/core/config.py`, `backend/app/integrations/sap_po/client.py`, `backend/tests/test_sap_po_integration.py`.
