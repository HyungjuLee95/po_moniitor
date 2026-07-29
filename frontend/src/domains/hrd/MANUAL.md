# HRD MANUAL

## Filter layout and selection

- Place corporation codes and table names in one filter panel immediately below I/F ID search.
- After the initial option lookup, select all values in both lists.
- When all options are selected, omit that query key to mean no filter.
- When a list has options but none are selected, do not run search or Excel export; ask the user to select at least one.

운영 서버 테스트 전송은 명확한 확인 절차를 거치고 XML·내부 URL을 화면에 노출하지 않는다. Excel은 인증 헤더가 포함된 Blob 요청으로 다운로드한다.

일일 점검은 `search_ifid=HRD` 인터페이스 현행과 최근 168시간 `DELIVERING` 메시지를 동시에 조회하며 어느 한쪽 실패도 성공으로 오인하지 않는다.

초기 진입 시 필터 없이 HRD 인터페이스를 한 번 조회하고 응답의 `company_cd`, `table_name`에서 중복을 제거해 체크박스 목록을 만든다. 초기 분석 문서는 법인코드 18개·테이블 6개라고만 명시하고 실제 식별자 전체를 열거하지 않으므로 값을 추정해 하드코딩하지 않는다. 사내 SAP 데이터가 원본이며 서버별로 목록이 자동 갱신된다.

법인코드는 backend의 기존 Set 완전 일치 규칙을 따른다. 아무것도 선택하지 않으면 전체, 하나 이상 선택하면 SQL의 법인코드 조합이 선택 조합과 정확히 같은 인터페이스만 조회한다. 테이블은 선택 목록 중 하나와 일치하면 조회한다.
