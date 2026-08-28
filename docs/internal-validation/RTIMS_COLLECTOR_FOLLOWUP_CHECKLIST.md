# RTIMS Collector 사용자가 별도로 확인할 최소 항목

## 이 파일을 사용하는 시점

먼저 `RTIMS_COLLECTOR_SOURCE_ANALYSIS_PROMPT.md`로 `src`, SQL XML, DDL, PL/SQL, 설정 파일과 테스트 fixture를 모두 분석한다.

그 결과 파일 `RTIMS_COLLECTOR_IMPLEMENTATION_ANALYSIS.md`에서 `FOLLOWUP_REQUIRED`로 판정된 항목만 이 문서에 옮긴다. 소스에서 분석 가능한 내용은 이 문서에서 다시 조사하지 않는다.

확인할 수 없는 항목이 많아도 괜찮다. 값을 추정하지 말고 다음 상태 중 하나로 작성한다.

- `CONFIRMED`: 담당자 또는 승인된 오프라인 자료로 확인
- `UNAVAILABLE`: 확인 권한·자료·담당자가 없어 확인 불가
- `UNKNOWN`: 아직 확인하지 않음
- `NOT_APPLICABLE`: 해당 환경에는 적용되지 않음

## 절대 안전 원칙

- LLM·자동화 도구를 운영·개발·품질·검증·DR 서버에 연결하지 않는다.
- 사용자가 직접 확인하거나 DBA/Basis가 제공한 오프라인 자료만 사용한다.
- 실제 message row, payload, Message ID, 인터페이스·채널·시스템 데이터는 조회하거나 전달하지 않는다.
- `.env`, 계정, 비밀번호, URL, IP, port, service name, token, 인증서 원문을 전달하지 않는다.
- DDL·DML·procedure·job·Collector·테스트 메시지·채널 제어를 실행하지 않는다.
- metadata 확인도 사내 승인 여부가 불명확하면 실행하지 않는다.
- 확인이 불가능하면 `UNAVAILABLE`로 남기며 억지로 채우지 않는다.

## 정말 별도 확인이 필요한 항목 요약

| 번호 | 항목 | 소스로 확인하기 어려운 이유 | 확인 불가 시 영향 |
|---:|---|---|---|
| 1 | 제공 소스와 현재 배포본 revision 일치 여부 | 현재 배포 상태는 저장소만으로 증명 불가 | 원본 동일성 보장 불가, source 기준 구현은 가능 |
| 2 | 실제 활성 Collector와 runtime override | DB/config에서 기본값을 덮어쓸 수 있음 | 보수적 기본값으로 개발 가능, 동일 운영주기 보장 불가 |
| 3 | source에 누락·충돌한 DB 객체 정의 | 운영 DB에만 body/index/constraint가 있을 수 있음 | 해당 객체를 쓰는 Collector 실연동 보류 |
| 4 | 서버별 SAP runtime parameter | SID별 host-id/WSDL variant가 외부 설정일 수 있음 | 해당 SAP source 호출 실연동 보류 |
| 5 | 운영 부하·보존·backfill 정책 | 코드가 아니라 운영 승인 사항 | 운영 자동 스케줄 활성화 보류 |
| 6 | shadow 검증 가능 환경 | 조직·인프라 승인 사항 | 운영 전환 판정 보류 |

이 여섯 범주 외의 질문은 1번 소스 분석으로 되돌린다.

## 1. 배포 revision 일치 여부

정확한 Legacy 동작 복제가 목표일 때만 확인한다.

| 질문 | 답변 | 상태 | 확인 근거 |
|---|---|---|---|
| 제공 source의 commit/tag/build version은 무엇인가? | `[작성]` | | manifest/version 파일 |
| 현재 배포본 version과 같은가? | `YES/NO/확인 불가` | | 버전 문자열만 작성 |
| DDL·PLSQL이 application과 별도로 배포됐는가? | `YES/NO/확인 불가` | | 배포 이력 존재 여부만 작성 |

서버명·설치 경로·계정은 기록하지 않는다.

확인이 불가능하면 다음처럼 작성한다.

```text
상태: UNAVAILABLE
영향: 제공 source 기준으로 구현 가능하나 현재 운영 배포본과 완전 동일하다고 보장할 수 없음
```

## 2. 실제 활성 Collector와 runtime override

1번 분석 결과가 source 기본값을 이미 확정했다면 **현재 값이 source와 다르다는 근거가 있을 때만** 작성한다.

실제 SID는 `SERVER-A`처럼 치환한다.

| 서버 별칭 | Collector type/class | 활성 여부 | override된 key | 마스킹된 값 | 상태 |
|---|---|---:|---|---|---|
| SERVER-A | `[작성]` | YES/NO | `[변경된 key만]` | `[숫자/boolean/객체명]` | |

확인이 필요한 key는 다음으로 제한한다.

- `TASK_INTERVAL`
- `LIMIT_COUNT`
- `FROM_TIME_SEC`, `TO_TIME_SEC`, `ADD_MILLISEC`
- `DELIVERY_SEMANTICS`
- `global.useHostId`
- `HOST_ID_TABLE`, `HOST_ID_FIELD`
- `ENABLE_SYNC`, `PERSIST_DURATION`
- worker/pool size
- timeout·retry 횟수

URL·host·계정·비밀번호는 필요하지 않다. 전체 설정 row를 복사하지 않고 위 값만 수기로 옮긴다.

확인이 불가능하면 source 기본값을 `OBSERVED_SOURCE_DEFAULT`로 사용하고 운영 활성화 전 확인 사항으로 남긴다.

## 3. source에 누락되거나 충돌한 DB 객체

이 절은 1번 분석 결과가 구체적인 객체를 `FOLLOWUP_REQUIRED`로 지정했을 때만 사용한다.

### 3.1 확인 대상 작성

| 객체 별칭 | 필요한 정보 | source에서 부족한 이유 | DBA 제공 가능 | 상태 |
|---|---|---|---:|---|
| `[분석 결과 ID]` | DDL/signature/body/index/constraint/grant | MISSING/CONFLICT | YES/NO | |

### 3.2 DBA에게 요청할 최소 metadata

분석 결과가 요구한 객체에 한해서 다음 중 필요한 것만 요청한다.

- 객체 type과 존재/status
- table/view 컬럼
- PK/UK/FK/check constraint
- index와 컬럼 순서
- sequence 정의
- procedure/function/package argument
- source에 없는 package body 또는 procedure source
- dependency·trigger·synonym
- scheduler job의 주기·활성 여부
- runtime 계정에 필요한 object privilege 종류
- 누락 객체의 `DBMS_METADATA.GET_DDL` 결과

실제 table row, distinct 값, 상태별 건수와 sample data는 요청하지 않는다.

### 3.3 DBA 요청문

아래 문구를 객체별로 전달한다.

```text
RTIMS Collector 재구현을 위해 아래 객체의 구조 metadata만 필요합니다.
실제 table row, 업무 데이터, bind 값, 계정·접속정보는 필요하지 않습니다.

- 대상 객체: <OBJECT_ALIAS>
- 필요한 항목: <DDL / COLUMN / CONSTRAINT / INDEX / ARGUMENT / SOURCE / GRANT 중 선택>
- 제공 형식: UTF-8 텍스트 또는 Markdown
- 마스킹: owner, tablespace, DB link, URL, host, 계정, 하드코딩 상수
- 금지: DDL 실행, DML 실행, sample row, distinct/group-by 결과
```

### 3.4 DBA용 선택적 metadata SQL

아래 SQL은 LLM이 실행하지 않는다. DBA가 승인된 객체 하나만 대상으로 필요한 쿼리만 선택한다.

```sql
-- 객체
select owner, object_name, object_type, status
from all_objects
where owner = upper(:owner)
  and object_name = upper(:object_name);

-- 컬럼
select column_id, column_name, data_type, data_length,
       data_precision, data_scale, nullable, data_default
from all_tab_columns
where owner = upper(:owner)
  and table_name = upper(:object_name)
order by column_id;

-- Procedure/Function/Package argument
select package_name, object_name, overload, position, sequence,
       argument_name, in_out, data_type, data_length,
       data_precision, data_scale, defaulted
from all_arguments
where owner = upper(:owner)
  and (object_name = upper(:object_name) or package_name = upper(:object_name))
order by package_name, object_name, overload, sequence;

-- Source에 없는 PL/SQL 정의
select name, type, line, text
from all_source
where owner = upper(:owner)
  and name = upper(:object_name)
order by type, line;

-- 승인된 객체의 구조 DDL export
select dbms_metadata.get_ddl(
         upper(:object_type), upper(:object_name), upper(:owner)
       ) as ddl
from dual;
```

추출 결과에 schema, tablespace, DB link, URL 또는 하드코딩된 접속정보가 있으면 전달 전에 마스킹한다. 추출된 DDL은 실행하지 않는다.

## 4. source에 없는 SAP 서버별 runtime parameter

현재 확인된 `getMessageLogs`의 DB 객체 오류를 해결하려면 source 분석 결과에 값이 없을 때만 다음을 확인한다.

| 서버 별칭 | delivery semantics | useHostId | host-id table | host-id field | cursor 형식 | limit | 상태 |
|---|---|---:|---|---|---|---:|---|
| SERVER-A | `[작성]` | | | | | | |

확인 우선순위:

1. Legacy properties/XML/seed SQL
2. `MON_COLLECTOR_PARAMS` 설정 정의 또는 마스킹된 수기 값
3. 기존 개발자 설명
4. Basis가 제공한 WSDL/XSD 오프라인 사본

값을 확인할 수 없다면 해당 `getMessageLogs` 실연동만 보류한다. 임의 테이블명이나 field를 만들지 않는다.

추가로 source에 로컬 WSDL/XSD가 없고 서버별 variant가 있다는 근거가 있을 때만 Basis에게 다음을 요청한다.

- URL을 제거한 WSDL/XSD 오프라인 사본
- 정확한 service/port/operation 이름
- 필요한 UME Role/Action 이름
- 인증·권한·DB 객체 오류의 fault code 분류

실제 endpoint와 사용자 할당 내역은 요청하지 않는다.

## 5. 코드 밖 운영 정책

운영 자동화 전 확인이 필요한 조직 결정이다. 확인할 수 없으면 `UNAVAILABLE`로 작성하고 보수적인 설정 제안까지만 진행한다.

| 정책 | 확인 질문 | 답변 | 상태 | 확인 불가 시 처리 |
|---|---|---|---|---|
| 동시성 | SID당 허용 가능한 동시 Collector 수 | | | 1로 제안, 운영 활성화 보류 |
| 호출 주기 | 허용 가능한 최소 poll interval | | | source 값 또는 보수값 제안 |
| Backfill | 허용 시간대·최대 범위·승인자 | | | 자동 backfill 비활성 |
| Retention | RTIMS 보존기간과 purge 담당 | | | purge 구현/활성화 보류 |
| 중단 기준 | timeout·오류율·지연 시 중단 조건 | | | circuit breaker 보수값 제안 |
| Payload/Audit | 상시 수집 허용 여부 | | | on-demand/비활성 기본값 |
| 수동 실행 | 실행 권한과 감사 필요 여부 | | | ADMIN + dry-run만 설계 |

실제 일 메시지량·상태별 건수·업무 peak 시각은 필수 답변이 아니다. 제공 불가하면 부하 계산식을 사용하고 숫자는 `UNKNOWN`으로 둔다.

## 6. Shadow 검증 가능 여부

| 질문 | 답변 | 상태 |
|---|---|---|
| 운영과 분리된 승인된 test SID가 있는가? | YES/NO/확인 불가 | |
| 기존 Collector 결과와 신규 결과를 구조·건수 수준에서 비교할 수 있는가? | YES/NO/확인 불가 | |
| test용 synthetic fixture를 사용할 수 있는가? | YES/NO/확인 불가 | |
| 운영 전환 전 승인 담당자가 정해져 있는가? | YES/NO/확인 불가 | |

실데이터 제공이 불가능하면 source fixture와 synthetic data로 기능·복구 테스트를 진행하고, 운영 동일성 판정은 보류한다.

## 7. 확인 불가 항목의 개발 영향

| 확인 불가 항목 | 그래도 개발 가능한 범위 | 보류할 범위 |
|---|---|---|
| 배포 revision | source 기준 전체 설계·단위 테스트 | 운영본 완전 동일 판정 |
| 활성 Collector 목록 | registry·scheduler·adapter 구현 | 운영 enable 목록 확정 |
| runtime override | 설정 우선순위와 보수 기본값 | 동일 주기·부하 보장 |
| 누락 DB 객체 | interface·fake repository·contract test | 해당 Oracle 실연동 |
| SAP host-id | source adapter interface와 mock | `getMessageLogs` 실호출 |
| 운영 부하 정책 | rate limit·circuit breaker 구현 | 운영 자동 스케줄 활성화 |
| Shadow 환경 | 단위·계약·synthetic 테스트 | 운영 전환 승인 |

확인 불가가 많아도 Collector framework 개발 전체를 중단하지 않는다. 단, 확인되지 않은 external contract를 성공으로 가정하거나 운영 연결을 활성화하지 않는다.

## 8. 최종 작성 양식

1번 분석 결과의 follow-up ID만 옮긴다.

| Follow-up ID | 위 1~6 분류 | 확인 결과 | 상태 | 마스킹 근거 | 개발 영향 |
|---|---|---|---|---|---|
| F-001 | `[분류]` | `[작성 또는 확인 불가]` | CONFIRMED/UNAVAILABLE/UNKNOWN/N/A | `[파일명/담당 역할]` | `[구현 가능/실연동 보류/운영 보류]` |

최종 확인:

- [ ] 소스에서 분석 가능한 내용을 사용자 조사로 넘기지 않았다.
- [ ] 실제 업무 데이터가 포함되지 않았다.
- [ ] 접속정보와 credential이 포함되지 않았다.
- [ ] LLM·자동화 도구가 서버 또는 DB에 접속하지 않았다.
- [ ] 확인 불가능한 항목을 추정하지 않았다.
- [ ] 각 미확인 항목의 개발 가능 범위와 보류 범위를 적었다.

작성 완료한 이 파일과 `RTIMS_COLLECTOR_IMPLEMENTATION_ANALYSIS.md`를 함께 전달한다.
