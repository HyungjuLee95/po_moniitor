# RTIMS MANUAL
연결값은 `RTIMS_ORACLE_*` 환경 변수로 관리한다. pool은 lazy 생성하고 SQL은 bind parameter만 사용한다. 기존 table/column 이름은 Oracle 원본을 유지하고 API DTO에서 소문자로 변환한다.
