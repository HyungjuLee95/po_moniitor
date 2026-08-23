# Configuration ERROR
시작 실패는 JSON 문법·중복 SID·environment·port를 확인한다. 서버 미표시는 enabled와 backend 재시작 여부를 확인한다.

## 2026-08-23 / 서버마다 다른 SAP PO 연결값을 표현하기 어려움

- 증상: 공통 SAP 계정과 공통 경로만 예시되어 서버별 host·port·계정·설치 경로 차이를 안전하게 설정하기 어려웠다.
- 영향: 한 SID의 연결값을 맞추면 다른 SID의 WSDL 또는 인증 호출이 실패할 수 있었다.
- 원인: `PoServer`의 서버별 계정 기능이 `.env.example`에 드러나지 않았고 서버별 endpoint path override 계약이 없었다.
- 해결: `PO_SERVERS_JSON`에 서버별 `base_url`, `port`, `username`, `password`, `endpoint_paths`를 정의하고 미지정 값만 공통 설정으로 fallback하도록 했다.
- 검증: config 단위 테스트, backend compileall, 프로젝트 문서 검증을 수행한다.
- 재발 방지: 신규 SAP 호출 경로는 공통 path 설정과 `endpoint_paths` 허용 키를 함께 갱신한다.
- 관련 파일: `backend/app/core/config.py`, `backend/app/integrations/sap_po/client.py`, `.env.example`.
