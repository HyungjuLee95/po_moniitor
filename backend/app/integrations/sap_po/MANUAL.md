# SAP PO Integration MANUAL

- SID는 `ServerRegistry`에서 검증한 뒤 client를 만든다.
- 서버별 `base_url`, `port`, 선택적 credential을 `PO_SERVERS_JSON`에서 읽는다.
- 서버 credential이 없으면 공통 `SAP_PO_USER/PASSWORD`를 사용한다.
- 서버별 credential은 공통값보다 우선하며 빈 값은 공통값으로 fallback한다.
- timeout, retry, TLS, 공통 WSDL path는 모두 `.env`로 변경 가능하다.
- 특정 SID의 설치 경로가 다르면 해당 서버 `endpoint_paths`의 SOAP 또는 HTTP 키만 덮어쓴다. URL host와 port는 항상 해당 서버의 `base_url`, `port`에서 만든다.
- SOAP/HTTP 예외는 내부 URL·credential을 제거한 `SapPoError`로 변환한다.
- Directory 비밀번호 endpoint는 ADMIN 전용 API에서만 호출한다.
