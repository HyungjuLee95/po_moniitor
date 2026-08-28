# Certificates ERROR

## 2026-08-23 / 서버별 KeystoreService 미배포

- 증상: KeystoreHelp는 정상 응답하지만 인증서 만료일을 제공하는 KeystoreService가 HTTP 404를 반환했다.
- 영향: View·Alias·DN 43건은 조회되지만 만료일·D-day·시리얼·서명 알고리즘은 확인할 수 없다.
- 원인: 해당 SAP PO 시스템에 PI/TPM KeystoreService가 배포 또는 기동되어 있지 않다.
- 해결: 전체 실패로 처리하지 않고 KeystoreHelp 결과를 유지하며 `expiry_available=false`, 상태 `UNKNOWN`, 마스킹된 안내를 반환한다.
- 검증: 임시 SAP 서버 read-only 호출과 FastAPI `/certificates`에서 200, 43건, KeystoreHelp `ok`, KeystoreService `not_found`를 확인했다.
- 재발 방지: 서버 온보딩 시 두 서비스를 독립 점검하고, KeystoreService가 없는 시스템을 정상적인 부분 지원 상태로 취급한다.
- 관련 파일: `backend/app/integrations/sap_po/keystore.py`, `backend/app/domains/certificates/service.py`.

## 2026-08-27 / 전체 권한 계정으로 KeystoreService 404 재확인

- 증상: 권한 확대 후에도 KeystoreHelp는 46건을 반환하지만 KeystoreService는 HTTP 404다.
- 영향: View·Alias·DN은 조회되나 만료일과 D-day는 계속 미확인이다.
- 원인: 계정 권한 문제가 아니라 해당 시스템의 서비스 배포 또는 endpoint path 문제라는 기존 판단이 강화됐다.
- 해결: 부분 지원 응답을 유지한다. 만료일이 필수이면 NWA 배포 상태와 서버별 `keystore_certificates` 경로를 Basis와 확인한다.
- 검증: FastAPI `/certificates` HTTP 200, 46건, `keystore_help=ok`, `keystore_certificates=not_found`, `expiry_available=false`를 확인했다.
- 재발 방지: 권한 변경 후에도 HTTP 404는 401/403과 분리해 서비스 존재 여부를 먼저 확인한다.
- 관련 파일: `backend/app/integrations/sap_po/keystore.py`, `backend/app/domains/certificates/service.py`.
