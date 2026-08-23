# Configuration API

`GET /configuration/bootstrap`, `GET/PUT /configuration/monitoring-policy`, `GET /configuration/rtims-check`, `GET /configuration/sap-po-check`를 제공한다. 공개 응답에는 내부 URL과 credential을 포함하지 않는다.

`rtims-check`는 Oracle 연결 후 RTIMS live API에 필요한 객체와 필수 컬럼을 `where 1=0`으로 점검하고 `objects[{object,ready}]`를 반환한다. 데이터 행과 bind 값은 조회하거나 응답에 포함하지 않는다.
