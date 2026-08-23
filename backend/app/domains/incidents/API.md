# Incidents API

`GET /api/v1/incidents?sid=&hours=&limit=&offset=`는 `incidents:read`, `PATCH /api/v1/incidents/{error_log_id}/resolve`는 `incidents:resolve`를 사용한다. 원본은 RTIMS `MON_ERR_HIST`이며 `MON_INTF_MAP`, `PM_INTERFACE`, `PM_INTF_GROUP`, `SYS_ERR_CODE`, `SYS_ERR_CATE`로 인터페이스·그룹·분류를 보강한다. 해결은 `ERR_STATE='C'`, `USER_ID`, `ERR_PROC_MSG`를 같은 트랜잭션에서 갱신한다.
