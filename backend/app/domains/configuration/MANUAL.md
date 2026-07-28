# Configuration MANUAL
서버 속성은 `PoServer`가 단일 계약이다. `public_view()`에는 SID·표시명·환경·capability만 포함하고 URL·credential을 제외한다. 응답시간 window·지연 기준·상세 건수는 `configuration.monitoring_policy`에서 관리하며 admin만 변경한다.

운영 모드 시작 시 `.env` registry의 서버 메타데이터를 `configuration.po_server`에 upsert해 사용자별 서버 FK와 동기화한다. 계정·비밀번호는 저장하지 않는다.
