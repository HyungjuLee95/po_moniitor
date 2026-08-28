# Certificates MANUAL

- KeystoreHelp `getKeystore`는 `keystoreHelpParameter xsi:nil="true"`로 전체 View·Alias·Subject/Issuer DN·키 여부를 조회한다.
- KeystoreService `GetKeystoreCertificates`는 시작일·만료일·시리얼·서명 알고리즘을 조회한다.
- 두 응답은 `(view, alias)`로 조인한다. KeystoreService가 미배포·권한 부족이면 KeystoreHelp 결과를 유지하고 상태를 `UNKNOWN`으로 표시한다.
- 상태는 `days_remaining < 0 → EXPIRED`, `<= warning_days → EXPIRING`, 그 외 `VALID`, 만료일 없음은 `UNKNOWN`이다.
- 서버별 경로가 다르면 `PO_SERVERS_JSON.endpoint_paths.keystore_help/keystore_certificates`로 덮어쓴다.
- 응답에는 credential, 내부 URL, 인증서 binary/private key를 포함하지 않는다.
