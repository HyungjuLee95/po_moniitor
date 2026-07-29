# HRD API

When every visible option is selected, the frontend omits `company_codes` or `table_names` and the backend performs an unfiltered lookup for that dimension. If visible options exist but selection is empty, the frontend does not call search or Excel APIs.

| 화면 기능 | API | 처리 |
|---|---|---|
| 목록·필터 옵션 | `GET /hrd/interfaces` | 최초 무필터 응답에서 법인코드·테이블 체크박스 옵션 추출 |
| Excel | `GET /hrd/interfaces/excel` | 인증 Blob 다운로드 |
| 테스트 메시지 | `POST /hrd/test-message` | OPERATOR 이상, 결과 상태 |
| 일일 점검 | `GET /hrd/interfaces?search_ifid=HRD`, `GET /messages?hours=168&status=DELIVERING` | 병렬 조회·부분 오류 |

법인코드와 테이블은 선택값마다 `company_codes`, `table_names` query key를 반복한다. 미선택은 해당 필터를 보내지 않는다. Excel 다운로드도 현재 체크박스 선택과 동일한 query를 사용한다.
