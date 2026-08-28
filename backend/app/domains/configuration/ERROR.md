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

## 2026-08-28 / Collector schema 예시가 식별자 검증에 실패

- 증상: `.env.example`을 실제 `Settings`로 읽을 때 `po_db_schema` 예시가 validation error를 발생시켰다.
- 영향: 예시 파일을 복사한 초기 설치에서 backend가 시작되지 않을 수 있었다.
- 원인: schema placeholder에 SQL 식별자로 허용하지 않는 하이픈을 사용했다.
- 해결: schema 예시를 영문자로 시작하는 대문자·underscore 식별자로 변경했다.
- 검증: Python 3.11.7 `Settings(_env_file='.env.example').po_servers`로 서버 2개와 profile 3개를 파싱한다.
- 재발 방지: `.env.example` 변경 시 문자열 검색만 하지 않고 실제 설정 모델 parsing을 검증한다.
