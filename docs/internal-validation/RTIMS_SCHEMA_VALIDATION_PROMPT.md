# RTIMS 사내 LLM 검증 프롬프트

아래 프롬프트를 사내 LLM에 그대로 전달한다. 분석은 제공된 소스·DDL·SQL XML·테스트 fixture·DBA metadata export만 대상으로 하며 LLM이 DB나 서버에 직접 접속하지 않는다. 실제 접속정보, 비밀번호, 메시지 payload와 개인정보는 결과에 포함하지 않는다. Collector 전체 재구현 조사는 `RTIMS_COLLECTOR_SOURCE_ANALYSIS_PROMPT.md`와 `RTIMS_COLLECTOR_FOLLOWUP_CHECKLIST.md`를 우선 사용한다.

```text
당신은 사내 RTIMS Oracle과 SAP PO Collector 소스의 계약을 감사하는 분석가다.
목표는 PO_MONITOR_MAIN 백엔드가 기존 Collector가 적재한 RTIMS 테이블을 정확히 조회하도록, 추정 없이 실행 가능한 계약을 확인하는 것이다.

[중요 규칙]
0. 100% 오프라인 정적 분석만 수행한다. 운영·개발·검증 서버, SAP, Oracle, HANA, PostgreSQL에 접속하거나 HTTP/SOAP/SQL/명령을 실행하지 않는다. 정보가 없으면 UNKNOWN으로 표시하고 DBA가 제공할 마스킹 metadata export를 요청한다.
1. runtime에서 실제 router가 호출하는 service/repository만 Live로 분류한다.
2. import되지 않거나 호출되지 않는 rtims_service.py, MON_BUF_* 기반 구형 코드는 Dead/Buffer로 별도 분류한다.
3. 근거가 없으면 추정하지 말고 UNKNOWN으로 표시한다.
4. 실제 host, service name, 계정, 비밀번호, 토큰, 메시지 payload, 개인정보는 출력하지 않는다.
5. SQL은 테이블명·컬럼명·bind 이름·조건·정렬·pagination이 보이도록 전체를 출력하되 실제 bind 값은 예시값으로 치환한다.

[확인 대상 API]
- 대시보드 메시지 요약과 채널 상태 요약
- 최근/실시간 메시지 목록과 동일 조건 count
- CPU/MEMORY 노드별 시계열
- Adapter Engine Queue와 MON_Q_STATUS 대기
- 시스템 그룹별 S/F/P/C 통계
- 채널명 검색 통계와 메시지 목록
- MON_ERR_HIST 장애 목록과 해결 UPDATE

[반드시 답할 질문]
1. 실제 reachable endpoint → router → service → SQL 파일/메서드 매핑을 표로 작성하라.
2. 다음 객체가 현재 운영 schema에 존재하는지와 owner, object type을 확인하라.
   MON_MSG_LOG, MON_INTF_MAP, MON_DAILY_STATISTICS, MON_DAILY_CLOSE_STAT,
   MON_CHANNINFO, MON_RES_USAGE, MON_RESOURCE, MON_AE_QUEUE, MON_Q_STATUS,
   MON_ERR_HIST, PM_INTERFACE, PM_INTF_GROUP, SYS_ERR_CODE, SYS_ERR_CATE.
3. 위 객체의 COLUMN_NAME, DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE,
   NULLABLE을 출력하라. 특히 MON_DAILY_CLOSE_STAT의 전체 DDL 또는 컬럼을 반드시 제공하라.
4. MON_DAILY_CLOSE_STAT의 시간 컬럼이 YMDD/HOUR인지, 건수 컬럼이 COUNT인지,
   INTF_MAP_ID와 어떤 키로 결합하는지 확인하라.
5. MON_MSG_LOG.MSG_STATUS의 코드와 의미를 소스 enum, procedure, SQL XML과 테스트 fixture에서 확인하라.
   S, F, P, I, C, DLVD 등의 실제 운영 건수·distinct 값은 조회하지 말고 근거가 없으면 UNKNOWN으로 표시하라.
6. MON_DAILY_STATISTICS.LATENCY/MAX_LATENCY가 합계, 평균, 밀리초, 초 중 무엇인지
   Collector 저장 코드 또는 프로시저 근거로 확인하라.
7. MON_MSG_LOG.REQ_ELAPSED_SEC/PROV_ELAPSED_SEC/RES_ELAPSED_SEC의 단위와
   화면 평균 응답 계산식이 REQ만인지 세 값 합인지 API별로 확인하라.
8. MON_RESOURCE.TYPE 값과 CPU/MEMORY 표기 대소문자를 소스·DDL·fixture에서 확인하라. 운영 distinct 조회는 하지 말라.
9. MON_RES_USAGE.MINUTE_DAY의 기준 timezone, 수집 간격, 하루 경계와 데이터 지연 시간을 확인하라.
10. MON_CHANNINFO.STATE와 MON_Q_STATUS.SEVERITY의 코드/의미를 소스·fixture에서 확인하고 운영 row는 조회하지 말라.
11. MON_ERR_HIST → MON_INTF_MAP → PM_INTERFACE → PM_INTF_GROUP 및
    SYS_ERR_CODE/SYS_ERR_CATE 조인의 실제 키와 INNER/LEFT JOIN 의도를 확인하라.
12. 장애 해결 시 허용되는 ERR_STATE 값, USER_ID 길이, ERR_PROC_MSG 제한,
    commit/rollback 및 UPDATE 권한을 확인하라.
13. Collector가 각 테이블을 갱신하는 주기, checkpoint/watermark, retention,
    purge 조건과 화면에서 허용할 데이터 freshness를 표로 작성하라.
14. SID 비교가 대소문자 무관이어야 하는지 소스 계약을 확인하라. 실제 SERVER_ID 목록·distinct 값은 출력하지 말라.
15. Oracle 버전과 OFFSET/FETCH 지원 여부, 관련 인덱스가 시간창·SID·채널 검색에
    사용 가능한지는 DBA가 제공한 마스킹 metadata/실행계획 사본이 있을 때만 확인하라.
16. 제공된 신규 DDL의 14개 테이블과 운영 원본 DDL을 비교하고 컬럼 타입·길이·정밀도,
    PK/UK/index, default, nullable 차이를 객체별로 출력하라.
17. PM_INTF_GROUP_ID, PM_INTF_ID, MON_INTF_MAP_ID, MON_MSG_LOG_ID,
    MON_RESOURCE_ID, MON_ERR_LOG_ID, SYS_ERR_CODE_ID, SYS_ERR_CATE_ID sequence의
    실제 이름, start/increment/cache/cycle 설정과 호출 SQL을 확인하라.
18. 현재 14개 객체 외에 Collector를 새 환경에서 완전히 실행하는 데 필요한
    MON_BUF_*, MON_COLLECTOR_*, payload, schedule 테이블과 procedure/package/job/trigger를
    누락 없이 목록화하고 원본 DDL 파일 위치를 제시하라.

[필수 결과 형식]
A. CONFIRMED / UNKNOWN / DEAD 요약
B. API→Live SQL 매핑표
C. 객체·컬럼 계약표
D. 상태코드·단위·timezone 표
E. 실행 가능한 최종 SQL(SQL-007~018), bind 타입과 예시
F. Collector 적재 주기·watermark·retention 표
G. 현재 PO_MONITOR_MAIN 구현과 다른 점을 Severity(CRITICAL/MAJOR/MINOR)로 정리
H. 추가로 필요한 원본 파일 또는 DBA 조회 목록
I. `backend/oracle/001_rtims_monitoring_schema.sql` 대비 정확한 DDL diff

다음 DBA 메타데이터의 마스킹된 오프라인 export가 입력으로 제공된 경우에만 근거로 사용하라. LLM이 직접 조회하지 않는다.
- ALL_OBJECTS 또는 USER_OBJECTS 객체 확인
- ALL_TAB_COLUMNS 컬럼 확인
- ALL_CONSTRAINTS/ALL_CONS_COLUMNS 키 확인
- ALL_IND_COLUMNS 인덱스 확인
- 실제 row, distinct 값, GROUP BY 건수는 요구하거나 조회하지 않음

결과에는 내부 주소와 자격 증명을 절대 포함하지 말라.
```

사내 LLM 결과를 외부로 옮길 때는 SQL 구조·컬럼·상태 의미만 남기고 실제 SID 목록, 사용자 ID, 오류 메시지와 데이터 샘플은 마스킹한다.
