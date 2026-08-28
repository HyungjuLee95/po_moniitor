# SAP PO Integration MANUAL

- SID는 `ServerRegistry`에서 검증한 뒤 client를 만든다.
- 서버별 `base_url`, `port`, 선택적 credential을 `PO_SERVERS_JSON`에서 읽는다.
- 서버 credential이 없으면 공통 `SAP_PO_USER/PASSWORD`를 사용한다.
- 서버별 credential은 공통값보다 우선하며 빈 값은 공통값으로 fallback한다.
- timeout, retry, TLS, 공통 WSDL path는 모두 `.env`로 변경 가능하다.
- 특정 SID의 설치 경로가 다르면 해당 서버 `endpoint_paths`의 SOAP 또는 HTTP 키만 덮어쓴다. URL host와 port는 항상 해당 서버의 `base_url`, `port`에서 만든다.
- WSDL import 또는 SOAP address가 DNS에서 해석되지 않는 short hostname을 발행하면 서버별 `host_aliases`에 해당 이름만 등록한다. HTTP session은 그 alias만 설정된 서버 origin으로 치환하며 외부 schema host는 변경하지 않는다.
- SOAP/HTTP 예외는 내부 URL·credential을 제거한 `SapPoError`로 변환한다.
- Directory 비밀번호 endpoint는 ADMIN 전용 API에서만 호출한다.
- 키스토어는 WSDL import에 의존하지 않고 검증된 SOAP envelope를 직접 POST한다. redirect를 따라가지 않고 응답 크기를 `SAP_KEYSTORE_MAX_RESPONSE_BYTES`로 제한한다.
- KeystoreHelp와 KeystoreService는 독립 호출한다. 한쪽만 실패하면 가능한 데이터로 저하 동작하고, 둘 다 실패할 때만 전체 API를 502로 처리한다.
