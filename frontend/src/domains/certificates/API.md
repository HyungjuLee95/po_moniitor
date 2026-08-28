# Certificates API

`GET /certificates?sid=&warning_days=`를 사용한다. 초기·기준 변경·새로고침 시 최대 75초 timeout으로 독립 호출하며, 오류 시 기존 인증서 값을 섞지 않고 명시적 실패 상태를 표시한다. `meta.notice`, `expiry_available`, `summary`, `services`를 부분 지원 안내에 사용한다.
