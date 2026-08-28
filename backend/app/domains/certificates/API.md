# Certificates API

`GET /api/v1/certificates?sid=&warning_days=30`은 SAP PO 키스토어 인증서 목록을 반환한다.

- 권한: `certificates:read`와 SID 접근 권한. 현재 ADMIN·OPERATOR에 허용한다.
- `warning_days`: 1~3650, 기본 30일.
- 원본: KeystoreHelp `getKeystore` + KeystoreService `GetKeystoreCertificates`.
- `data[]`: `sid`, `view`, `alias`, `kind`, `subject_dn`, `issuer_dn`, `not_before`, `not_after`, raw date, `serial_number`, `signature_algorithm`, `days_remaining`, `status`, `sources`.
- `meta`: count, views, warning_days, expiry_available, 상태별 summary, service별 안전한 상태, notice, source.
- KeystoreService만 실패하면 HTTP 200 부분 결과를 반환하고, 두 서비스가 모두 실패하면 502다.
- credential, endpoint URL, 인증서 binary와 private key는 반환하지 않는다.
