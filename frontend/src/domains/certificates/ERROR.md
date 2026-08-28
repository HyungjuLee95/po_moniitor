# Certificates ERROR

만료일이 모두 미확인이면 API `meta.expiry_available`과 `services.keystore_certificates`를 먼저 확인한다. 전체 조회 실패는 SAP PO 계정의 AS Java 키스토어 조회 권한과 두 서비스 경로를 확인한다.
