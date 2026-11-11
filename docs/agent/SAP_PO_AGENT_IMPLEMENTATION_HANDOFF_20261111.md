# SAP PO 모니터링 개선과 개발 자동화 에이전트 인계서

- 문서 작성일: 2026-11-11, Asia/Seoul.
- 대상 저장소: `HyungjuLee95/po_moniitor`.
- 코드 조사 기준: 로컬 `main`의 HEAD `4053f8406fc2d3fe818c83cd6d694a50774eef2a`와 당시 작업 트리. 이 SHA만으로 미커밋 변경까지 재현되지는 않는다.
- SAP 실증 기준: 2026-10-14~19에 보존한 화면·통신·설치 계약·로컬 probe. 현재 본사 서버의 상태를 새로 확인한 결과가 아니다.
- 문서 목적: 본사 개발 에이전트가 기존 기능을 유지하면서 확인된 읽기 수집을 접목하고, SAP 변경 없이 개발 자동화의 계획·검증 프로토타입을 만들 수 있게 한다.
- 배포 형태: UTF-8 Markdown 한 파일. SAP SDK JAR, 원본 WSDL, HAR, 계정·쿠키·업무 데이터는 포함하지 않는다.

## START 1 에이전트가 먼저 알아야 할 결론

기존 프로젝트에는 채널 조회·제어, 메시지·Audit, 트래픽·리소스·Queue, RTIMS Collector, 인증·서버 권한, 인터페이스·Topology, Excel, 인증서, HRD, 장애·알림 UI가 이미 있다. 이번 작업의 중심은 화면을 중복 신설하는 일이 아니라 데이터 원본·상태 의미·완전성·최신성·실패 복구를 정확하게 연결하는 것이다.

실제 외부 수집 근거가 있는 것은 세 경로다.

1. NWA System Overview의 AS Java 지표 44개: 독립 Python 로그인·세션 사용·로컬 쿠키 상실 후 복구까지 확인했다. 자연 idle/SSO 만료와 모든 인증 실패 분기는 미검증이다.
2. 표준 AdapterMessageMonitoring 메시지 메타데이터: Basic 인증 조회를 확인했다. 반환 목록 길이나 `number`를 전체 업무 건수로 간주할 수 없고, 상한·시간 경계·중복·보존 범위를 별도로 검증해야 한다.
3. ChannelAdminServlet의 `action=status`: 목록·필터·단건과 XML 구조를 확인했다. 시작/정지, 건강 상태, 제어 방식은 서로 다른 필드다. 전체 노드·모든 Adapter Engine의 전역 인벤토리임을 입증한 것은 아니다.

CPA·잡·TREX·보존 정책에는 화면·문헌·일부 읽기 근거가 있지만, 모두 독립 수집을 완료한 상태가 아니다. 이름이 비슷한 DB 테이블을 연결해 필드를 임의 생성하지 않는다.

개발 자동화는 Python 계획기와 Directory SOAP, 별도 Java ESR 작업기로 설계할 수 있다. 로컬에서 초기화 7단계와 모델·매핑 13개 시나리오를 검증했으나, 원격 ESR 인증·서버 저장·컴파일·활성화·Directory 실제 생성 성공은 검증하지 않았다. **141개 준비 항목은 완료율이 아니라 구현과 남은 검증의 목록**이다.

## START 2 이 문서를 적용하는 범위

| 단계 | 본사 에이전트가 진행할 일 | SAP에 미치는 범위 |
|---|---|---|
| 오프라인 코드 개선 | 상태 정규화, parser, DTO, 저장 구조, UI, fake transport, 테스트 | SAP 호출 없음 |
| 오프라인 자동화 프로토타입 | manifest, 참조 DAG, 단순 매핑, plan/diff, 미리보기·내보내기 | SAP 호출 없음 |
| 기존 승인 범위의 읽기 검증 | 본사에서 확인한 SID·origin·계정·원본 계약으로 제한된 조회 | 읽기 operation만 허용 |
| 향후 샌드박스 작성 | 실제 객체 저장·검사·활성화·readback | 현재 기본 범위 밖. 독립 테스트 환경과 명시된 작성 범위 필요 |

이 문서는 다음 SAP 작업을 실행하라는 지시가 아니다: 설정·권한·로깅·보존 정책 변경, 채널 Start/Stop 또는 제어 모드 변경, 메시지 재전송·취소, payload 조회, 잡 실행, CPA refresh, TREX 활성화·재색인, 테스트 메시지 전송, 객체 Create/Change/Activate/Delete/Revert/강제 잠금 해제. 기존 제품에 해당 기능이 있어도 이번 읽기 개선 검증에서 호출하지 않는다.

브라우저를 수집기의 상시 실행 기반으로 사용하지 않는다. 기존 분석에서 Web Dynpro 애플리케이션 세션 한도에 도달했다. 네트워크 수집은 서비스별 독립 HTTP 세션으로 구현하고, 사람의 브라우저 쿠키를 복사하거나 새 탭을 반복 생성하지 않는다. 필요한 브라우저 관찰은 본사에서 정한 기존 탭과 범위 안에서만 수행한다.

## START 3 증거 표시와 경로 규칙

| 표시 | 뜻 | 완료로 주장할 수 없는 범위 |
|---|---|---|
| `REMOTE_READ_VERIFIED` | 과거 대상 설치에서 실제 읽기 응답을 확인 | 현재 본사 서버·다른 SP·전체 노드 동등성 |
| `LOCAL_VERIFIED` | 메모리 모델·직렬화·오프라인 validator 또는 로컬 probe 성공 | 서버 wire 수락·실제 업무 동작 |
| `CONTRACT_OBSERVED` | 설치 WSDL·XSD·배포 클래스·화면 계약 확인 | 권한·실제 API 실행 성공 |
| `PROPOSED` | 앞으로 구현할 DTO·API·테이블·알림·복구 설계 | 현재 저장소에 이미 존재하거나 배포됐다는 주장 |
| `UNVERIFIED` | 원본 계약 또는 실행 결과가 미확정 | 없음·정상·지원 불가의 단정 |

- `PROJECT_ROOT`: 본사에서 clone한 `po_moniitor` 저장소. 이 문서의 `backend/...`, `frontend/...`는 이 위치 기준이다.
- `RESEARCH_ROOT`: 별도로 반입한 원본 조사 자료의 루트. `pimon-analysis-20261014`, `20261015`, `20261018`, `20261019` 폴더와 이전 통합 문서를 이 아래에 둔다.
- `PO_ORIGIN`: 운영자가 백엔드 설정으로 제공하는 `https://<승인된-host>:<port>` 형태의 실제 origin. 본 문서에는 예시 `https://po.example.invalid:50001`만 사용한다.
- `SID`: 운영자가 등록한 논리 서버 ID. 예시 `POX`은 실제 계정·서버가 아니다.
- 원본 내부의 옛 절대 경로를 그대로 실행하지 않는다. 원본 파일과 SHA를 보존하고, 별도의 작업 사본에서 경로를 재바인딩한다.
- 본 문서에서 제안한 route·테이블명·enum은 SAP API와 구분한다. 현재 코드에 존재하는지 재검색하고 충돌 시 저장소의 현재 계약에 맞춘다.

## START 4 본사 반입 및 첫 실행 전 확인

1. 이 Markdown을 읽고 저장소 `AGENTS.md → PROJECT.md → CURRENT_TASK.md → 영역 문서 → 대상 도메인 README/MANUAL/SKILL/ERROR/API → 코드·테스트` 순서를 따른다.
2. 현재 작업 트리·브랜치·HEAD를 확인한다. 본 문서를 만든 로컬 저장소에도 기존 미커밋 변경이 있었다. `reset --hard`, `clean`, 전체 staging으로 이를 덮어쓰지 않는다. 새 브랜치나 격리된 작업 디렉터리에서 필요한 변경만 만든다.
3. 의존성 버전은 본사 저장소의 lock·문서를 기준으로 다시 확인한다. 조사 당시 기준은 Python 3.11.7, FastAPI, Next.js 16.2.12, React 19.2.7, PostgreSQL 17 권장이었다. 문서 반입을 이유로 의존성을 일괄 최신화하지 않는다.
4. 실제 origin·인증·TLS 신뢰·SID·권한·RTIMS 사용 여부는 본사 설정으로 공급한다. 기존 비밀번호를 복사하지 않는다. 프런트엔드에 host·계정·원본 XML·쿠키를 전달하지 않는다.
5. 앱 전체 startup에 Collector scheduler가 붙을 수 있으므로 단순 계약 확인을 위해 서버를 먼저 켜지 않는다. 앱을 import하거나 테스트하기 전 해당 fixture·startup hook이 실제 외부 시스템을 호출하는지 확인한다.
6. 기본은 네트워크 없는 fixture 테스트다. 실서버 읽기는 operation allowlist, timeout, 응답 크기·시간 구간·행 수 상한, 단일 실행 잠금, 비밀값 없는 증거 보존을 준비한 뒤 진행한다.
7. 설치 WSDL/XSD는 본사 계정으로 승인된 GET 경로에서 다시 얻고 fingerprint를 기록한다. 익명화·재직렬화한 공유 WSDL을 그대로 Zeep proxy 생성에 쓰지 않는다. QName prefix 선언이 생략된 검토 snapshot이 있다.
8. 수집 가능성을 확인하기 위해 SAP 설정을 켜거나 권한을 임의 확대하지 않는다. 불충분한 경우 `permission_denied`·`unverified`·`partial`과 필요한 계약을 보고한다.

현재 코드가 어떤 외부 분기를 사용하는지는 `.env`를 이 문서에 기재하지 않고 내부에서 확인한다. 과거 데모 응답·합성 fixture·오프라인 모델 성공은 실제 본사 데이터로 표시하지 않는다.

## START 5 한 파일만 가져갔을 때 가능한 것과 추가 원본

이 Markdown만으로 상태 정규화·공통 DTO·계획기·테스트·UI 및 문서에 제시한 호출 형태의 구현을 시작할 수 있다. 동일한 SAP SDK 로컬 probe의 재현에는 아래 내부 자료가 별도로 필요하다.

| 원본 | 필요 이유 | GitHub에 포함했는가 |
|---|---|---|
| 본사 설치에서 내려받은 원본 WSDL/XSD | 정확한 QName·wrapper·binding·service address | 아니오. 본사 내부 제한 저장소에 보관 |
| 해당 서버의 Repository/Directory JNLP·허용된 SDK JAR | ESR 클래스·리소스·클래스패스 재현 | 아니오. 권한·라이선스·버전을 확인해 내부 반입 |
| 원본 `implementation-readiness` runner/probe와 결과 | 7+13 로컬 검증 재현 | 아니오. 이 문서는 명령·계약·결과 범위만 설명 |
| 익명화된 요청·응답 fixture | 과거 parser와 실패 분기의 회귀 확인 | 원문 파일은 별도. 문서에는 예시와 검증 조건만 수록 |
| 원본 조사 폴더·SHA 목록 | 미확정 사항과 근거 추적 | 내부 자료로 별도 반입 |
| 본사 연결·권한·TLS 설정 | 실제 승인된 읽기 대상 선택 | GitHub에 저장하지 않음 |

공개 문서만 clone한 에이전트는 없는 SDK나 runner를 이미 가진 것처럼 행동하면 안 된다. 원본이 없으면 명시적으로 `missing_internal_artifact`를 기록하고, SDK가 필요 없는 오프라인 계획기와 mock 계약 검증부터 구현한다.

## START 6 권장 구현 순서와 산출물

1. **P0 신뢰성:** live 경로의 샘플 fallback, UNKNOWN→Running 변환, Directory 배열 parser, 조회 상한을 전체 건수로 표시하는 부분부터 보완한다.
2. **P1 읽기 provider:** 검증된 표준 메시지 조회와 ChannelAdminServlet status를 설정 기반 provider로 추가한다. 기존 RTIMS·Systatus 경로를 명시적인 source 선택·범위와 함께 유지한다.
3. **P1 지표:** NWA 세션 기반 44개 지표 수집기를 추가하고 자연 만료·인증 실패·부분 지표를 구분한다.
4. **P2 이력·사건:** snapshot/변화 이벤트, 알림 확인·복구, source freshness와 completeness를 API/UI에 연결한다.
5. **P2 자동화 프로토타입:** manifest→참조 DAG→제한된 모델→검증→plan/diff→내보내기를 SAP 호출 없이 완성한다.
6. **P3 관리 수집:** CPA·각 잡 family·TREX·보존의 원본 계약을 따로 검증해 제공 가능한 필드만 추가한다.
7. **후속 샌드박스:** ESR 원격 인증과 최소 1:1 객체 세트 저장·컴파일·활성화·readback, Directory 작성과 복구를 별도 단계로 수행한다.

에이전트의 각 결과에는 변경 파일·공개 계약 영향·실행한 테스트·외부 호출 수·검증된 서버 범위·남은 미확정 항목을 남긴다. 실행하지 않은 시험을 PASS로 쓰지 않는다. 요구사항 개수를 성공률로 환산하지 않는다.

## START 7 신규 관측 DTO의 단일 계약

아래는 **새로 추가하는 관측 API v1의 제안 계약**이다. 기존 route 응답을 일괄 교체하라는 뜻이 아니다. APP·MON·MGT 장의 예시는 provider 내부 결과 또는 초기 설계 표현을 포함하므로 최종 경계에서 이 계약으로 변환한다. 본사 저장소에 이미 동등한 정식 계약이 있으면 migration/version 전략을 먼저 결정한다.

| 필드 | canonical 값 또는 의미 | 예시 표현의 변환 |
|---|---|---|
| `collection_status` | `not_collected/collecting/collected/partial/failed` | `COLLECTED`, `ok`는 `collected`; 인증 의심은 `failed`와 별도 `error_category` |
| `freshness` | `unknown/fresh/stale` | `current`는 `fresh`; 첫 수집 전에는 `unknown` |
| `completeness` | `unknown/partial/complete_for_query` | `UNKNOWN_GLOBAL_SCOPE`는 `unknown`과 limitations로 보존. 전역 전체성으로 승격하지 않음 |
| `health` | `unknown/healthy/degraded/unhealthy/not_applicable` | 수집 성공과 별도 평가. raw ChannelState·지표 state는 그대로 보존 |
| `support` | `unverified/supported/partial/unsupported` | 계약의 제공 범위. 해당 시도의 부분 수집과 다른 축 |
| `provider_id` | 자체 구현의 stable ID | 실제 SAP operation 이름과 분리 |
| `source_service` | SAP 서비스 또는 DB provider 이름 | 예: ChannelAdminServlet. 실제 origin은 응답에서 제외 |
| `source_kind` | `sap_http/sap_soap/db/demo` 등 versioned 원천 분류 | demo는 live와 명시적으로 분리 |
| `source_role` | `configuration_store/runtime_cache/runtime_status/history/mirror` | 같은 서버에서 읽어도 필드별 역할을 혼합하지 않음 |
| `last_attempt_at` | 가장 최근 수집 시도 시각 | 실패해도 갱신 가능 |
| `collected_at` | 현재 표시 중인 data snapshot을 수집 완료한 시각 | 실패 시 마지막 성공 snapshot의 시각 유지 |
| `last_success_at` | 가장 최근 유효 수집 성공 시각 | 실패·HTML·인증 의심·계약 오류로 전진하지 않음 |
| `returned_count` | 현재 snapshot에 실제 확보한 항목 수 | 첫 수집 전 `null`; 검증된 유효 빈 목록이면 `0` |
| `total_count` | 동일 조회 범위의 원본이 보장한 총수 | 미제공·상한·전역 미확정이면 `null` |
| `source_time/node_scope/query_window` | 확인된 원본 시각·노드 범위·조회 조건 | 모르는 값을 현재 시각·전체 노드로 채우지 않음 |

`complete_for_query`는 해당 요청 정의·필터·시간 구간을 검증한 범위의 의미다. 모든 엔진·노드·보존 영역·업무 건수의 전역 완전성을 자동 보장하지 않는다. 실패 시 data 배열이 비어 있다는 사실만으로 유효 0건을 표시하지 않는다.

이력의 개발 순서는 **P0 decoder/상태·식별 정확도 → 별도 snapshot/event 저장 작업 → 알림 연결**이다. APP-P01의 이력 항목은 후속 저장 작업으로 분리할 수 있고 P0 parser 수정의 완료 조건을 새 이력 전체 구축으로 불필요하게 확장하지 않는다.

## NAV 문서 목차

- [START 1 에이전트가 먼저 알아야 할 결론](#start-1-에이전트가-먼저-알아야-할-결론)
- [START 2 이 문서를 적용하는 범위](#start-2-이-문서를-적용하는-범위)
- [START 3 증거 표시와 경로 규칙](#start-3-증거-표시와-경로-규칙)
- [START 4 본사 반입 및 첫 실행 전 확인](#start-4-본사-반입-및-첫-실행-전-확인)
- [START 5 한 파일만 가져갔을 때 가능한 것과 추가 원본](#start-5-한-파일만-가져갔을-때-가능한-것과-추가-원본)
- [START 6 권장 구현 순서와 산출물](#start-6-권장-구현-순서와-산출물)
- [START 7 신규 관측 DTO의 단일 계약](#start-7-신규-관측-dto의-단일-계약)
- [APP 1 현재 코드 기준과 본사 작업 시작 절차](#app-1-현재-코드-기준과-본사-작업-시작-절차)
- [APP 2 현재 기능과 REA 결과의 연결표](#app-2-현재-기능과-rea-결과의-연결표)
- [APP 3 수정할 핵심 심볼과 코드 근거](#app-3-수정할-핵심-심볼과-코드-근거)
- [APP 4 P0 첫 작업은 실데이터와 샘플 및 미수집의 분리](#app-4-p0-첫-작업은-실데이터와-샘플-및-미수집의-분리)
- [APP 5 P0 채널 상태와 인벤토리 parser를 먼저 바로잡기](#app-5-p0-채널-상태와-인벤토리-parser를-먼저-바로잡기)
- [APP 6 P1 메시지 provider와 집계 범위 보완](#app-6-p1-메시지-provider와-집계-범위-보완)
- [APP 7 P1 지표 44개와 별도 세션 수집기의 통합](#app-7-p1-지표-44개와-별도-세션-수집기의-통합)
- [APP 8 P1 실제 알림과 확인 저장 연결](#app-8-p1-실제-알림과-확인-저장-연결)
- [APP 9 P2 설정 비교와 인터페이스 운영 문맥](#app-9-p2-설정-비교와-인터페이스-운영-문맥)
- [APP 10 P2 개발 자동화 plan-only 프로토타입](#app-10-p2-개발-자동화-plan-only-프로토타입)
- [APP 11 polling 동시성 및 권한을 함께 지키기](#app-11-polling-동시성-및-권한을-함께-지키기)
- [APP 12 구현 순서와 완료 판정](#app-12-구현-순서와-완료-판정)
- [APP 13 본사에서 실행할 검증과 기록](#app-13-본사에서-실행할-검증과-기록)
- [APP 14 본사 에이전트에 붙여넣을 작업 지시문](#app-14-본사-에이전트에-붙여넣을-작업-지시문)
- [APP 15 이 장의 재확인에 사용할 저장소 자료](#app-15-이-장의-재확인에-사용할-저장소-자료)
- [MON 1 모니터링 조사 결과를 구현에 사용하는 방법](#mon-1-모니터링-조사-결과를-구현에-사용하는-방법)
- [MON 2 AS Java 44개 지표의 정확한 요청 계약](#mon-2-as-java-44개-지표의-정확한-요청-계약)
- [MON 3 NWA 자동 로그인과 세션 복구](#mon-3-nwa-자동-로그인과-세션-복구)
- [MON 4 표준 SOAP 메시지 메타데이터 수집](#mon-4-표준-soap-메시지-메타데이터-수집)
- [MON 5 ChannelAdminServlet 상태 수집](#mon-5-channeladminservlet-상태-수집)
- [MON 6 공통 전송과 수집 결과 계약](#mon-6-공통-전송과-수집-결과-계약)
- [MON 7 에이전트용 구현 순서와 수용 기준](#mon-7-에이전트용-구현-순서와-수용-기준)
- [MON 8 원본 근거 위치와 무결성 확인](#mon-8-원본-근거-위치와-무결성-확인)
- [AUT 1 목적과 검증 경계](#aut-1-목적과-검증-경계)
- [AUT 2 첫 프로토타입의 지원 범위](#aut-2-첫-프로토타입의-지원-범위)
- [AUT 3 완전한 최소 논리 명세](#aut-3-완전한-최소-논리-명세)
- [AUT 4 계획기·검증 알고리즘](#aut-4-계획기검증-알고리즘)
- [AUT 5 SDK 환경 고정과 본사 재현](#aut-5-sdk-환경-고정과-본사-재현)
- [AUT 6 ESR bootstrap·인증·세션](#aut-6-esr-bootstrap인증세션)
- [AUT 7 ESR 객체 키·참조·모델](#aut-7-esr-객체-키참조모델)
- [AUT 8 Directory wire 계약](#aut-8-directory-wire-계약)
- [AUT 9 Channel typed DTO와 합성 예제](#aut-9-channel-typed-dto와-합성-예제)
- [AUT 10 ICO750/legacy와 참조 투영](#aut-10-ico750legacy와-참조-투영)
- [AUT 11 ChangeList의 요청·응답](#aut-11-changelist의-요청응답)
- [AUT 12 secret·원형 DTO·ReadContext](#aut-12-secret원형-dtoreadcontext)
- [AUT 13 Python backend와 Java worker의 경계](#aut-13-python-backend와-java-worker의-경계)
- [AUT 14 durable journal·충돌·멱등성](#aut-14-durable-journal충돌멱등성)
- [AUT 15 실행 상태·재시도·취소](#aut-15-실행-상태재시도취소)
- [AUT 16 결과·Active·Cache 성공 판정](#aut-16-결과activecache-성공-판정)
- [AUT 17 구현 묶음과 수용 기준](#aut-17-구현-묶음과-수용-기준)
- [AUT 18 본사 반입 자료와 출처](#aut-18-본사-반입-자료와-출처)
- [MGT 1 관리 수집은 서로 다른 원본으로 나눈다](#mgt-1-관리-수집은-서로-다른-원본으로-나눈다)
- [MGT 2 CPA 호출과 UME에서 확인할 사항](#mgt-2-cpa-호출과-ume에서-확인할-사항)
- [MGT 3 잡 수집의 최소 필드와 조사 순서](#mgt-3-잡-수집의-최소-필드와-조사-순서)
- [MGT 4 보존 정책과 TREX](#mgt-4-보존-정책과-trex)
- [MGT 5 DB 분석은 설치 schema가 준비된 뒤 진행한다](#mgt-5-db-분석은-설치-schema가-준비된-뒤-진행한다)
- [MGT 6 자체 관측 저장과 UI 연결](#mgt-6-자체-관측-저장과-ui-연결)
- [MGT 7 운영 시험과 완료 조건](#mgt-7-운영-시험과-완료-조건)
- [MGT 8 공개 1차 문헌과 해석 범위](#mgt-8-공개-1차-문헌과-해석-범위)
- [REF 1 141개 구현 준비 항목 전체](#ref-1-141개-구현-준비-항목-전체)
- [REF 2 Repository SDK 45개 파일의 당시 pin](#ref-2-repository-sdk-45개-파일의-당시-pin)
- [REF 3 KBA 3549157에서 확보한 테이블명 174개](#ref-3-kba-3549157에서-확보한-테이블명-174개)
- [REF 4 핵심 원본 파일과 SHA-256](#ref-4-핵심-원본-파일과-sha-256)
- [REF 5 본사 에이전트 완료 보고 형식](#ref-5-본사-에이전트-완료-보고-형식)

## APP 1 현재 코드 기준과 본사 작업 시작 절차

이 장은 `PO_MONITOR_MAIN`의 **현재 코드가 제공하는 기능과 조사 결과를 연결하는 구현 지도**다. 2026-11-11 KST에 파일을 읽어 확인했으며 애플리케이션, 테스트, SAP, DB를 실행하지 않았다. 실제 배포 환경의 설정과 운영 분기는 확인하지 않았다. 이 장의 개선 항목은 구현 완료 보고가 아니다.

| 기준 | 확인 값 또는 해석 |
|---|---|
| 대상 저장소 | `HyungjuLee95/po_moniitor` |
| 조사한 로컬 HEAD | `4053f8406fc2d3fe818c83cd6d694a50774eef2a` |
| 조사한 브랜치 | `main` |
| 작업 트리 | 기존 수정·미추적 파일 존재. HEAD만으로 작업 트리 전체를 고정한 것은 아님 |
| 주요 런타임 계약 | Python `3.11.7`; 공식 Next.js `16.2.12`; React `19.2.7`; npm `11.13.x`; Node engine `>=22.13.0` |
| 실제 SAP 조사 시점 | 별도 MON/AUT 절의 2026-10-14~19 보존 증거. 11월의 현재 서버 상태와 동일하다는 보장은 없음 |
| 경로 표기 | 이 장의 모든 소스 경로는 `PROJECT_ROOT` 기준 상대경로 |

본사 에이전트는 먼저 `AGENTS.md → PROJECT.md → CURRENT_TASK.md → 영역 README/MANUAL/SKILL → 대상 도메인의 README/MANUAL/SKILL/ERROR/API → 관련 코드·테스트` 순서로 읽는다. 문서에 적힌 줄 번호는 이 조사 스냅샷의 길잡이이며, 다른 커밋에서 그대로 patch 위치로 사용하면 안 된다. 실제 심볼과 호출 경로를 다시 검색한다.

조사 시 이미 변경된 파일은 `CHANGELOG.md`, `CURRENT_TASK.md`, `ERROR.md`, `ROADMAP.md`, `docs/INSTALL_INTERNAL_NETWORK.md`, `docs/architecture.md`, `frontend/package.json`, `frontend/package-lock.json`이었다. `docs/decisions/ADR-003-management-observation.md`와 `docs/plans/`도 미추적 상태였다. 이 문서를 적용한다는 이유로 이 변경을 삭제·덮어쓰기·일괄 커밋하지 않는다. 본사에는 본사 checkout의 상태를 기준으로 새 작업 브랜치를 만들고, 필요한 문서와 코드만 명시적으로 선택한다.

`CURRENT_TASK.md=IDLE`은 현재 기능의 운영 검증 완료를 뜻하지 않는다. 실제 구현을 시작할 때 본사 에이전트가 작업 목표·수정 범위·변경 금지 대상·완료 기준을 새로 기록한다. 이 인계 문서를 만드는 과정에서는 대상 프로젝트의 `CURRENT_TASK.md`를 수정하지 않았다.

## APP 2 현재 기능과 REA 결과의 연결표

아래의 “구현”은 코드·API·화면의 존재를 말한다. 실제 사내 서비스에서 모든 경로가 성공한다는 의미가 아니다. 특히 샘플 데이터, 미확정 외부 계약, 부분 지원과 실데이터를 분리해야 한다.

| 기능 | 현재 구현 | 조사로 추가 확보한 근거 | 접목 결과와 남은 경계 |
|---|---|---|---|
| 채널 상태 | `ChannelService.list_status()`가 Systatus `getChannInfo` 호출; 목록·검색·상세·제어 UI | `ChannelAdminServlet?action=status` 실제 응답, activation/health/control 분리 | 기존 화면의 상태 정확도 개선, 별도 provider 대조, 지속 시간·복구 이력. 전체 AE/노드 완전성은 별도 확인 |
| 채널 인벤토리 | CommunicationChannelIn `Query/Read`, 시스템별 drill-down | Query의 `CommunicationChannelID[]` shape와 Directory 계약 | 응답은 있는데 0건이 되는 parser 문제를 먼저 수정. 그 위에 구성 비교·업무 연결 확장 |
| 채널 Excel | ADMIN export와 업로드 비교 preview | 속성 namespace·테이블·모듈 순서·키 계약 | 기존 네 필드 비교를 비밀값 제외 typed snapshot diff로 확장. 현재 preview를 SAP 설정 적용기로 취급하지 않음 |
| 메시지·Audit | RTIMS 또는 AAE 최근 목록, 상태·기간·키워드, Message ID Audit UI | 표준 AdapterMessageMonitoring 목록의 실제 Basic 수집·상한·0건 대조 | AAE HOST_ID 계약과 독립된 조회 provider 추가. Audit은 이미 있는 기능을 재사용 |
| 트래픽·처리 결과 | RTIMS 시간/일 bucket, 성공·실패·대기·크기·지연·시스템 통계 | SOAP 목록의 제한과 집계 범위 실증 | 표본 길이와 전체 건수 분리, 원천/기간/권한/완전성 표시. SQL count 경로를 무조건 SOAP 추정값으로 교체하지 않음 |
| 리소스·Queue | RTIMS CPU/Memory, 시계열·Queue API와 UI | AS Java 지표 44개 실제 응답과 인증 복구 | 시스템 지표 provider·시계열 추가. 44개가 메시지·채널·CPA·Queue 전체를 대체하는 것은 아님 |
| 자동 Collector | HANA→Oracle profile, profile 없는 SOAP/PostgreSQL 호환 경로, opt-in scheduler, checkpoint·로그 | 독립 NWA form 로그인·세션 재사용·로컬 쿠키 상실 복구 | 새 읽기 provider의 수집 상태·신선도 추가. 기존 Oracle 원자적 transaction과 checkpoint는 유지 |
| 장애·알림 | RTIMS incident→alert 변환, drawer·확인 UI/API | 채널·메시지·지표를 사건 입력으로 사용 가능 | 실제 사건 저장, dedup, 확인 영속화, 복구 이력. 조사 자체가 알림 규칙을 완성한 것은 아님 |
| 인터페이스·Topology | BusinessSystem `Query`, InterfaceMonitor `getAllInterfaces`, RTIMS topology | ICO·SI·OM·채널 참조 구조 | 초기 명시적 업무 매핑 후 실제 읽기로 관계 보강. ESR 내부 key를 Directory DTO에 그대로 넣지 않음 |
| 인증서 | KeystoreHelp + KeystoreService, 만료·임박·UNKNOWN 분류 | 서비스별 부분 지원을 보존하는 기존 사례 | 공통 관측 envelope 설계에 재사용. 별도 서비스 미배포를 권한·정상 만료일로 바꾸지 않음 |
| HRD 점검 | 채널 기반 조회·Excel·선택 HANA 스케줄·Delivering 일일 점검 | 검증된 메시지·채널 읽기 경로 | 업무별 읽기 점검 프로필로 일반화. HRD 테스트 메시지 전송은 별도 쓰기 기능으로 유지 |
| LLM 분석 | 허용 문맥을 JSON API로 보내는 중계 adapter | 시각·범위·상태가 있는 관측 결과를 분석 문맥으로 활용 가능 | 근거를 붙인 분석 제안. 모델/RAG가 이미 완성됐거나 원인이 입증됐다는 뜻은 아님 |
| 공통 기반 | JWT·역할·SID 접근·capability, 사용자 대시보드·즐겨찾기·게시글·workspace | 새로운 SAP 계약과 직접 관계 없는 기존 기반 | 새 화면·API도 동일 권한 경계를 사용. 운영자 역할을 SAP 쓰기 포괄 허가로 해석하지 않음 |
| CPA/잡/TREX/보존 | 독립 관리 수집기는 발견되지 않음 | 별도 관리 화면·문헌·후보 원본 조사 | 계약 검증 후 provider별 추가. 관리 계획 문서 존재를 구현으로 세지 않음 |
| 개발 자동화 | DT~OM/Channel/ICO 작성기 없음 | AUT 절의 로컬 모델·SOAP 계약·141개 요구사항 | 첫 구현은 plan-only. 서버 생성·컴파일·활성화와 원격 무인 ESR 인증은 미검증 |

## APP 3 수정할 핵심 심볼과 코드 근거

| 상대 경로와 심볼 | 확인한 동작 | 구현 시 주의 |
|---|---|---|
| `backend/app/core/config.py:12`, `Capability` | `monitor/channel-control/audit/collector/hrd` Literal | 새 provider capability를 쓰려면 validation·bootstrap·UI gating·테스트를 함께 확장 |
| `backend/app/core/config.py:14`, `SapPoEndpointName` | 허용 endpoint 이름을 제한 | 임의 URL을 프런트 요청으로 받지 말고 승인된 backend registry에 추가 |
| `backend/app/core/config.py:77`, `PoServer` | SID·서버별 설정·host aliases·collector profile | `public_view()`에는 비밀·실제 origin·endpoint가 없음. 이 경계를 유지 |
| `backend/app/core/config.py:284`, `Settings.rtims_configured` | RTIMS 활성화와 host/service/user/secret 설정 유무 검사 | `DEMO_MODE`, `SAP_PO_LIVE_MODE`와 별개. “미설정”과 실제 연결 장애를 혼동하지 않음 |
| `backend/app/core/security.py:87`, `require_server_access` | 요청 SID와 사용자 allowed SID 비교 | 새 read API에도 필수. 저장 event의 SID 검증은 resource를 읽은 뒤 별도로 필요 |
| `backend/app/domains/configuration/registry.py:22`, `require_capability` | 활성 서버 존재 + capability 검사 | 새 provider 선택에도 서버 활성·권한·지원 여부를 모두 검사 |
| `backend/app/integrations/sap_po/client.py:30`, `rewrite_host_alias` | 명시 alias만 configured origin으로 치환 | 모든 host를 blanket rewrite하지 않음. 주소 변조와 외부 redirect를 허용하지 않음 |
| 같은 파일 `build_session():85` | Basic session, GET/HEAD/OPTIONS만 transport retry | SOAP POST 전체 retry를 추가하면 향후 쓰기까지 중복될 수 있음 |
| 같은 파일 `soap_client():104` | SID+service별 LRU Zeep client, `strict=False` | 자격정보·계약 변경 시 cache invalidation, session/thread 소유권 검토 필요 |
| `backend/app/integrations/sap_po/normalize.py:33`, `records` | 예상 필드 하나라도 있으면 부모 객체를 record로 취급 | 알려진 Query 배열을 이 범용 탐색기로 처리하면 잘못된 0건이 발생 |
| `backend/app/domains/channels/service.py:37`, `_status` | ERROR/FAIL→Error, STOP/INACTIVE→Stopped, 나머지→Running | 빈값·UNKNOWN·UNREGISTERED까지 정상처럼 축약할 수 있음 |
| 같은 파일 `inventory():98` | Query wrapper→범용 records→ID 추출 | 전용 typed parser 우선. Party·native ID 보존 |
| 같은 파일 `detail():140` | ReadContext=User, 속성을 name→value dict로 평탄화 | 작성 DTO·snapshot 원형으로 재사용 금지. namespace 중복·table·module 손실 가능 |
| `backend/app/domains/messages/service.py:16`, `list_recent` | AAE getMessageLogs, HOST_ID 설정 전달, client 필터 | HOST_ID 미확정 원인은 임의 DB 객체 이름으로 해결하지 않음 |
| 같은 파일 `audit():115` | getMessagesByIDs→getLogEntries | 이미 고정된 optional 인자·key suffix 계약 보존 |
| `backend/app/domains/messages/router.py:13`, `list_messages` | RTIMS count 또는 fallback `len(rows)` | fallback에서 offset은 전달되지 않고 meta에는 표시됨. 진짜 pagination인지 구분 필요 |
| 같은 파일 `count_messages():70` | fallback 최대 1000개 길이를 count로 사용 | 완전 count로 표시 금지 |
| `backend/app/domains/monitoring/service.py:15`, `summary` | SAP live+RTIMS 없음이면 최근 최대 1000개를 messages_today로 사용 | 오늘 전체·완전 통계라는 오해를 수정 |
| `backend/app/domains/alerts/router.py:55`, `acknowledge_alert` | 확인 결과 JSON만 반환 | 실제 저장과 저장 resource의 SID ACL 필요 |
| `backend/app/domains/collectors/scheduler.py:70`, `run_once` | 활성 SID/profile 순차 실행·고정 지연 | UI polling마다 수집기를 새로 만들지 않음 |
| `frontend/src/core/refresh.ts` | dashboard 15분, UI 요청 timeout 12초 | timeout과 수집 주기는 다른 개념. 실제 호출 증폭을 측정 |
| `frontend/src/domains/messages/RealtimeInterfacesPage.tsx:52` | 전용 메시지 화면 15초 갱신 | 모든 위젯이 15초라고 설명하지 않음 |
| `frontend/src/domains/dashboard/OperationsWorkspace.tsx:41` | 독립 widget fetch, 최초 실패 mock 대체 | 운영 데이터 실패를 정상처럼 보이는 mock으로 가리지 않음 |

## APP 4 P0 첫 작업은 실데이터와 샘플 및 미수집의 분리

### APP 4.1 현재 분기에서 확인한 문제

`MonitoringService.throughput/performance/resources/queues/system_statistics/system_queue_status`는 RTIMS가 설정돼 있으면 repository를 호출하고, 아니면 샘플값을 반환한다. 이 분기 자체는 `DEMO_MODE`·`SAP_PO_LIVE_MODE`를 확인하지 않는다. `slow_messages`도 RTIMS 미설정이면 샘플 목록을 만들며, RTIMS 오류 시에는 demo mode에 따라 오류 또는 샘플로 갈린다. 따라서 본사 설정에 따라 서로 다른 원천이 동시에 보일 수 있다. 현재 `.env`를 읽지 않았으므로 사용자의 화면이 지금 어느 분기를 실행 중인지는 이 조사에서 판정하지 않았다.

프런트 `OperationsWorkspace`도 최초 summary·channel 실패에 `fallbackSummary/fallbackChannels`를 넣고, 최초 alerts 실패에 `mockAlerts`를 넣는다. 이후 refresh 실패 때 기존 성공값을 유지하는 정책은 유용하지만, 원천 시각과 실패 상태를 함께 표시하지 않으면 오래된 값을 최신으로 오인할 수 있다.

### APP 4.2 APP-P00 구현 요구

1. sample/실수집/미설정/지원 안 됨/오류를 공통 DTO에서 구분한다. 운영 모드에서 실제 호출 실패를 sample success로 바꾸지 않는다.
2. 유효한 0건, 지원하지만 아직 한 번도 수집 안 됨, 인증 실패, 계약 오류, 부분 결과, 마지막 정상값만 남음은 서로 다른 상태다.
3. `0`, `[]`, `100% 정상`을 오류의 기본값으로 만들지 않는다. 알 수 없는 값은 nullable과 사유로 전달한다.
4. 원천 선택은 SID와 서비스별 명시 설정·capability를 사용한다. global RTIMS 설정 하나가 모든 provider의 준비 상태를 대표하지 않게 한다.
5. 기존 `{data, meta}` REST 계약을 가능한 한 유지하면서 meta를 추가한다. 프런트 타입·API 문서·consumer를 같은 변경에서 갱신한다.
6. 최초 오류는 오류/미설정 화면, refresh 오류는 마지막 성공값+stale 표시로 처리한다. SID 전환 시 이전 SID의 값을 새 SID 수치로 재사용하지 않는다.

아래 envelope는 **새 제품 설계 예시이며 SAP 응답 원문도 현재 구현된 DTO도 아니다.** 값은 가짜 예시다.

```json
{
  "data": [],
  "meta": {
    "sid": "POX",
    "source_service": "channel-admin-status",
    "source_kind": "sap_read",
    "contract_version": "channel-status-v1",
    "collection_status": "not_collected",
    "collected_at": null,
    "last_success_at": null,
    "source_time": null,
    "stale": null,
    "stale_after_seconds": null,
    "completeness": "unknown",
    "query_window": null,
    "returned_count": null,
    "total_count": null,
    "limitations": ["first collection has not completed"],
    "error_category": null
  }
}
```

`collected_at`은 수집 완료 시각이고 SAP 내부의 사건 시각은 `source_time`이다. 첫 수집 전 `stale=false`를 정상의 의미로 사용하지 않는다. `returned_count`는 현재 응답 배열 길이일 뿐 전체 count가 아니다. 계약과 해당 원천의 범위가 확인돼야 `completeness=complete`를 쓸 수 있다.

APP-P00 수용 시험: RTIMS 설정 유무×SAP live on/off×demo on/off의 조합을 fake repository로 검사한다. 정상 0건, 미설정, 401, Fault, timeout, 계약 불일치, 부분 결과의 DTO와 UI가 각각 구별돼야 한다. SID A 성공 후 SID B 실패에서도 A의 수치가 B의 최신값으로 보이지 않아야 한다. sample 데이터를 실제 수집 source로 반환하면 실패다.

## APP 5 P0 채널 상태와 인벤토리 parser를 먼저 바로잡기

### APP 5.1 APP-P01 상태 모델 보완

Systatus raw 상태와 servlet raw 상태를 무조건 하나의 enum으로 합치지 않는다. source별 decoder를 만들고 원문 상태를 보존한다. servlet은 `activation_state`, nullable `channel_state`, `control`을 각각 저장한다. `STARTED+ERROR`, `STARTED+INACTIVE`, `STOPPED+ChannelState 부재`를 서로 다른 결과로 유지한다. Systatus에서 얻지 못한 축을 추정해서 채우지 않는다.

기존 `status`를 소비하는 UI가 많으므로 새 정밀 필드와 별도로 compatibility presentation 값을 제공할 수 있다. 이때 unknown/missing을 Running으로 만들지 않고 UI에 확인 필요로 표시한다. summary의 `running = total - errors - stopped`도 unknown 항목을 정상에 포함하므로 함께 수정한다. 전체 enum에 대응하지 못하면 API는 raw+unknown을 반환하고, 화면은 경고 범주를 사용해야 한다.

snapshot key는 `(sid, engine_scope, native_channel_id)`처럼 실제 확인한 ID와 범위를 기본으로 한다. Systatus의 표시 이름·servlet의 ChannelID·Directory의 Party/Component/Channel tuple은 별도 필드와 검증한 매핑으로 유지한다. UI의 현재 `id=index`는 일시 표시용이며 영속 이력 key가 아니다. 앞뒤 공백·대소문자 정규화를 하더라도 원형 ID는 보존한다.

상태 변화 저장은 첫 snapshot baseline과 이후 변화 event를 구분한다. `first_observed_at`은 실제 장애 발생 시각이 아닐 수 있으며 polling 사이 구간은 정확한 사건 시각으로 단정하지 않는다. 부분 목록에서 사라진 채널을 삭제·복구 완료로 판정하지 않는다. STOPPED가 의도된 운용 정책일 수 있으므로 중요도·운용 시간·유지 조건 없는 전체 stopped 알림을 만들지 않는다.

APP-P01 수용 시험: fixture에 OK/ERROR/INACTIVE/UNKNOWN/UNREGISTERED/빈값/미지 코드를 넣고 각각의 raw 보존과 UI를 검사한다. STARTED+ERROR를 정상으로 표시하거나 INACTIVE를 STOPPED로 저장하면 실패다. 부분 snapshot과 다른 engine scope에서도 채널 삭제·복구 event가 잘못 생기지 않아야 한다. Start/Stop·automation change 호출 수는 0이어야 한다.

### APP 5.2 APP-P02 Query 배열 parser 수정

`channels/ERROR.md`의 미해결 기록은 `CommunicationChannelQueryOut → CommunicationChannelID[]`가 실제 응답인데 `records()`가 부모 wrapper 자체를 record로 고르는 문제다. `records()`의 전역 동작을 바꾸기 전에 이 operation 전용 parser를 추가하는 것이 영향 범위를 줄인다.

처리 순서:

1. Zeep 객체를 serialize한 뒤 예상 root/wrapper와 `CommunicationChannelID` 필드의 shape를 검사한다.
2. ID 목록을 명시적으로 펼친다. 0건·단건 객체·여러 건 배열의 형태를 fixture로 분리한다. 서버 계약이 배열만 보장하면 비정상 단건 객체를 엄격히 거부하는 정책도 명시한다.
3. 각 항목의 `PartyID` optional, `ComponentID/ChannelID` 필수 여부를 계약에 맞게 검증한다. wrapper 자체는 ID record가 아니다.
4. 원문 건수·변환 건수·거부 건수를 별도 검사한다. raw 항목이 있는데 결과가 0건이면 정상 empty보다 계약 오류로 분류한다.
5. `component_id=*`의 기존 `xsd.SkipValue` 생략 wire 계약을 보존한다. Query용 생략 특례를 Create DTO의 필수 key 검증으로 복사하지 않는다.
6. nonempty Party와 동일 이름/다른 Component 항목이 손실 없이 남는지 확인한다.

수정 후보: `ChannelService.inventory/_channel_id`, `normalize.py`의 호출부, `backend/tests/test_sap_po_integration.py`. 공통 normalizer를 바꾼다면 Systatus·Audit·InterfaceMonitor·BusinessSystem fixture도 함께 회귀 검사한다. 기존 tests의 축약 dict가 실제 wrapper 결함을 통과시킬 수 있으므로 실제 shape를 모사한 fixture를 우선한다.

## APP 6 P1 메시지 provider와 집계 범위 보완

### APP 6.1 APP-P03 표준 목록 provider 추가

현재 `MessageService.list_recent`의 live 경로는 AAE `getMessageLogs`에 cursor, delivery semantics, HOST_ID_TABLE/FIELD, limit을 보낸다. 미확정 HOST_ID DB 객체를 임의 값으로 채우거나 권한을 더 주면 해결된다고 가정하지 않는다. MON 절에서 실증한 표준 AdapterMessageMonitoring 목록 조회를 별도 provider로 추가한다.

권장 후보 파일은 `backend/app/integrations/sap_po/message_monitoring.py` 등이며 파일명은 설계안이다. 기존 `soap_client`·host alias·server registry·secret 경계를 재사용하되, operation별 typed request와 response를 둔다. 프런트는 SAP origin 또는 SOAP operation명을 지정하지 않는다. provider 선택이 실패할 때 다른 종류의 조회를 무조건 재시도해 결과 범위를 바꾸지 않는다. 선택 경로와 제한은 API meta에 남긴다.

`MessageService.audit`는 이미 `getMessagesByIDs` 뒤 `getLogEntries`를 호출한다. `referenceIds/correlationIds`, archive, key suffix, maxResults, olderThan, locale 계약을 임의로 간소화하지 않는다. 목록 provider를 바꿔도 Audit의 검증된 흐름을 유지하고, 목록의 기술 ID와 Audit이 요구하는 messageKey를 구분한다. 로그 내용을 수집할 권한과 목록을 볼 권한은 같은 의미가 아니다. payload 읽기는 기본 범위에서 제외한다.

APP-P03 수용 시험: 인증된 정상 0건·정상 목록·SOAP Fault·401·HTML 응답·알 수 없는 wrapper를 구분한다. 응답 metadata를 DTO에 보존하며 업무 body를 반환하지 않는다. HOST_ID 미설정 fixture에서도 표준 provider는 그 AAE 인자에 의존하지 않아야 한다. existing Audit 인자 회귀와 no-resend/no-cancel을 transport spy로 검사한다.

### APP 6.2 APP-P04 count와 pagination의 의미 수정

현재 `messages/router.py`의 RTIMS 경로는 조건이 일치하는 SQL count를 별도로 구한다. 이 경로는 그대로 보존한다. RTIMS 없는 경로는 목록 길이를 `total`로 쓰고 offset을 실제 목록 조회에 전달하지 않는다. `/messages/count`도 최대 1000개 길이에 의존한다. `MonitoringService.summary`의 `messages_today` 역시 최대 1000개 최근 목록 길이다. 이 값들을 완전한 전체 합계로 노출하지 않도록 계약을 분리한다.

새 provider에는 `returned_count`, `total_count(nullable)`, `completeness`, `cap_reached`, `query_window`, `warning`, `permission_warning`, `caller_scope`, `source_service`를 둔다. XSD에 total/paging이 없는 서비스를 offset API처럼 포장하지 않는다. local cache를 기반으로 pagination한다면 “해당 수집 snapshot 내 pagination”이라고 명시한다. 지원되지 않는 offset을 조용히 무시하고 같은 첫 페이지를 반환하면 안 된다.

기간 분할과 중복 제거는 단순히 전날부터 반복 호출하는 기능이 아니다. 고정 timezone·from/to의 경계·정렬·원본 식별자·버전/방향·관측 시점·수집 gap을 정의한다. archive/current 영역을 구분하고, caller 가시성과 AE 범위 밖의 데이터를 전체 업무 건수에 포함했다고 표시하지 않는다. `logVersion` 필터가 기대대로 제한하지 않았던 과거 관측도 있으므로 필터 이름만 믿고 dedup key를 제거하지 않는다.

완전한 일 집계를 제공하지 못하는 첫 버전은 `최근 조회 N건`, `현재 수집 범위의 오류율`, `부분 집계`처럼 범위를 표시한다. 수치 0을 장애나 정상으로 판정하는 규칙은 해당 시간·필터의 성공한 완전 조회를 전제로 한다. 원천이 바뀌면 같은 그래프라도 이전과 이후의 count 정의가 다를 수 있으므로 source와 contract revision을 함께 저장한다.

APP-P04 수용 시험: cap 1/10/100, 경계 시각의 동일 message, 여러 logVersion, 지연 도착·반복 수집·정상 0건·권한 경고·부분 scope fixture를 사용한다. 부분 결과로 전체 count/100% 성공률을 표시하면 실패다. RTIMS SQL count의 기존 조건 일치와 frontend pagination 회귀도 확인한다.

## APP 7 P1 지표 44개와 별도 세션 수집기의 통합

### APP 7.1 APP-P05 별도 provider 경계

지표 SOAP는 기존 Basic client에 URL만 추가하면 끝나는 기능이 아니다. 이번 설치에서 Basic 요청은 HTTP 200의 빈 응답을 냈고, NWA 로그인 문맥의 수집은 44개를 반환했다. 기존 `SapPoSession`은 Basic 세션이므로 NWA form 로그인·CookieJar와 복구 상태를 가진 전용 provider가 필요하다. 기본 로그인 계정 인증과 SAP 인증을 혼동하지 않는다. 앱의 Bearer JWT를 SAP에 전달하지 않는다.

새 지표 provider는 MON 절의 44개 정의 집합과 일치성 검사를 재사용한다. 원시 monitorValue, textMonitorName, monitorName, state, aggregation을 보존하고, 지표별로 확인한 변환만 적용한다. 모든 값을 동일 단위로 바꾸거나 모든 state/aggregation 코드의 의미를 추정하지 않는다. response 44개가 있어도 중복·누락·비숫자·Fault이면 정상 수집으로 처리하지 않는다.

한 `(sid, auth profile, provider)`마다 session과 로그인 single-flight를 관리한다. UI 사용자·위젯마다 SAP 로그인을 새로 만들지 않는다. 세션 캐시는 credential generation·endpoint contract 변경 시 폐기한다. 설정 변경 후 기존 LRU Zeep session이 이전 자격정보를 재사용하는 문제도 함께 다룬다. 여러 worker에서 공유할 수 없는 requests Session은 소유권을 명시한다.

자연 idle/SSO 만료, form 없는 SSO 복원, 401/403, 잘못된 비밀번호, 변경된 login form, 부분 지표 응답은 추가 검증 대상이다. 로컬 쿠키 상실 후 재로그인 성공을 서버 자연 만료 전 경로의 검증으로 표현하지 않는다. 반복 로그인은 process 단위뿐 아니라 서버·계정 전체의 제한과 cooldown을 고려한다. 잘못된 자격정보로 무한 로그인하지 않는다.

### APP 7.2 APP-P06 기존 Collector와 원자성 보존

이미 `CollectorScheduler`와 HANA→Oracle 수집기가 있다. 이를 무시하고 화면마다 별도 daemon과 scheduler를 만들지 않는다. 신규 provider의 실행 주기·single-flight·실행 상태를 기존 수명주기와 조정하되, 기존 pipeline의 DB transaction 경계를 바꾸지 않는다.

Oracle profile은 HANA page `(timestamp,message_id)` 안정 정렬, Oracle buffer, `process_msg_logs`, checkpoint, 성공 로그를 한 Oracle transaction으로 처리한다. 이 checkpoint를 지표·CPA·잡 관측의 진도로 재사용하지 않는다. management/metric 관측은 별도 PostgreSQL 모델과 성공 시각을 사용한다. profile 없는 `monitoring.collector_checkpoint`도 SID 단일 key이므로 여러 서비스 상태를 덮어쓰는 용도로 사용하지 않는다.

새로운 provider key를 사용하는 `collection_run/latest_observation` 같은 테이블은 설계안이다. 실제 migration 작성 전에 현 DB catalog와 기존 migration을 확인한다. 현재 migrations는 001~006까지 존재하므로 다음 번호를 본사 checkout에서 다시 계산한다. 이미 적용된 migration을 수정하지 않는다. 원본 메시지·인증 쿠키·비밀번호·raw 로그인 form을 저장하지 않는다.

현재 scheduler 잠금은 process 내부다. 분산 lease가 없는데 backend 여러 개에서 같은 수집을 실행하지 않는다. 향후 다중 인스턴스 지원에는 owner/expiry/fencing·unique run identity·crash 회복 시험이 필요하다. 죽은 worker의 lease를 근거 없이 빼앗거나 데이터 수집 실패를 성공 checkpoint로 전진시키지 않는다.

APP-P05/P06 수용 시험: 한 번의 collector job이 최초 로그인→44개, 같은 session 재사용, 쿠키 상실→제한된 복구를 수행하는 fake flow를 검증한다. 동시에 여러 UI가 요청해도 로그인·수집이 중복 폭증하지 않아야 한다. provider 장애가 기존 HANA/Oracle checkpoint·commit·다른 SID 수집을 바꾸면 실패다. shutdown event가 대기와 bounded 호출을 종료하고 신원·자격정보 변경 후 이전 세션이 재사용되지 않아야 한다.

## APP 8 P1 실제 알림과 확인 저장 연결

### APP 8.1 APP-P07 이미 있는 스키마를 먼저 활용

`backend/migrations/002_dashboard_alert_llm.sql`에는 이미 `monitoring.alert_event`와 `acknowledged_at`, `acknowledged_by`, status, SID index가 있다. “알림 확인 테이블이 없다”는 가정으로 중복 schema를 만들지 않는다. 현재 ACK route는 이 테이블을 쓰지 않고 응답만 반환한다. 실제 적용 DB에 해당 migration이 있는지 확인한 뒤 repository/service를 연결한다.

RTIMS alert ID는 `error_log_id`를 문자열로 변환한 값이고 local `alert_event`의 identity와 같다고 보장되지 않는다. source_system/source_event_id/local_event_id를 구분하고, 외부 사건 원본을 별도 참조로 보존한다. ACK는 도구 내 사용자의 확인이며 RTIMS 장애 해결 또는 SAP 상태 변경과 다르다. 자동으로 incident resolve를 호출하지 않는다.

ACK 구현 순서:

1. 요청 사용자의 `alerts:acknowledge` permission 검사.
2. alert ID로 저장 resource를 조회하고 존재·원천·SID 확인.
3. 저장 resource의 SID에 대한 사용자 접근 권한 검사. client가 보낸 sid만 믿지 않음.
4. transaction에서 현재 상태·version을 확인하고 확인 시각/사용자와 감사 정보를 기록.
5. 같은 사용자의 반복 ACK가 중복 사건을 만들지 않게 하고, 동시에 resolve된 event를 다시 open으로 되돌리지 않음.
6. commit된 값을 반환하고 새 요청 또는 재시작 뒤에도 유지되는지 검증.

현재 route에는 SID/resource lookup이 없으므로 permission만 추가해서 충분하다고 판단하면 안 된다. unauthorized/unknown resource의 HTTP 정책은 기존 보안 정책과 일관되게 정하고 테스트한다. 단순히 `require_server_access` dependency를 붙이기 위해 임의 query SID를 추가하면 resource SID 불일치 문제가 남을 수 있다.

### APP 8.2 APP-P08 사건 규칙과 UI

첫 규칙은 중요 채널의 ERROR 지속·상태 변화, 성공한 완전 집계 범위의 메시지 실패 증가, 수집 자체 실패처럼 해석 가능한 조건부터 시작한다. source별 상태·완전성·신선도 없이 “0건이면 장애” 규칙을 만들지 않는다. expected operating window, 중요도, 지속 횟수/시간, cooldown, dedup key, recovery 조건을 명시한다. 반복 로그 row와 독립 장애 사건을 구분한다.

동일 사건은 하나의 event를 갱신하고 last_seen·occurrence_count를 보존한다. 첫 관측·정상 복귀·수집 누락을 각각 구분한다. 알림 ACK가 장애 복구를 뜻하지 않고, 수집 실패가 채널 ERROR를 뜻하지 않는다. 알림 UI에서 마지막 근거 시각·source·scope를 열 수 있어야 한다. 외부 메신저 전송은 별도 integration과 수신자 설정이 필요한 후속 기능이며 이 프로토타입에 자동 발송을 포함하지 않는다.

APP-P07/P08 수용 시험: ACK 후 reload·서비스 재시작, 동일 ID/다른 SID 접근, viewer/operator/admin 조합, 동시 ACK/resolve, repeated detection, stale input, first baseline, maintenance window, recovery를 검증한다. API 실패 시 `mockAlerts`를 실제 사건처럼 표시하면 실패다. 12초 UI timeout은 한 widget만 실패 처리하고 다른 성공 결과를 지우지 않아야 한다.

## APP 9 P2 설정 비교와 인터페이스 운영 문맥

### APP 9.1 APP-P09 typed 구성 스냅샷

현재 `ChannelBulkService`의 비교 필드는 `dbuser/dbpassword/connectionURL/adapter_type` 네 개이고 preview는 설정을 SAP에 적용하지 않는다. 현재 `ChannelService.detail`은 같은 Name의 속성을 덮어쓸 수 있는 dict를 만든다. 이 결과를 전체 채널 정의 또는 생성 DTO로 선언하면 안 된다.

새 read adapter는 scalar `(Name,Namespace?,Value?)` 배열, table row/cell, ordered module process steps, parameter groups를 원형으로 보존한다. Read의 administrative fields와 restricted 작성 DTO를 구분한다. `ReadContext=User`가 Active 내용과 다를 수 있으므로 context를 노출한다. 같은 키라도 다른 draft/active version은 다른 snapshot이다.

설정 diff는 비밀값을 제거한 canonical model과 normalizer version으로 계산한다. Module 순서·table 행·QName·Namespace를 의미 없이 정렬하거나 대소문자를 통합하지 않는다. 읽기에서 빈 secret은 실제 unset의 증거가 아니므로 `unknown/unset/provided`를 구분한다. 기존 ADMIN 비밀 Excel 기능을 자동 snapshot 수집 경로에 재사용해 평문 비밀을 저장하지 않는다.

인증서 조회는 기존 `(view,alias)`와 UNKNOWN 부분 지원 계약을 재사용한다. 인증서가 어느 채널에 사용되는지 연결하려면 실제 해당 adapter의 keystore 참조 필드를 확인해야 한다. 별도 KeystoreService가 없는데 날짜를 추정하거나 새 서비스를 자동 배포하지 않는다.

### APP 9.2 APP-P10 업무/인터페이스 연결

`InterfaceService`의 BusinessSystem 목록·Namespace inventory는 기존 구현이다. RTIMS topology 미설정 시 데모 edge를 반환하는 분기도 APP-P00의 source 구분 대상이다. 완전한 ESR→ICO 자동 연결이 이미 구현된 것처럼 안내하지 않는다.

첫 운영 화면은 명시적인 업무/담당자/중요 채널 매핑으로 시작할 수 있다. 이후 authorized Directory read로 ICO와 channel tuple을 확인해 source/target SI·operation·OM 관계를 추가한다. native channel runtime ID와 Directory tuple을 실제 매핑한 근거가 필요하다. 이름 substring 일치만으로 모든 메시지를 특정 채널의 처리량으로 확정하지 않는다. 현재 채널별 RTIMS SQL의 `%channel_id%` 매칭은 이 정확도 검증 대상이다.

LLM의 현재 `sanitize_context` allowlist는 id/sid/title/detail/domain/severity/status/시각 중심이다. 새 지표·timeline을 넘기려면 크기 제한·마스킹·source/time/completeness가 포함된 새로운 typed context와 provider 계약을 정의한다. arbitrary raw XML이나 메시지 body를 전달하지 않는다. LLM의 원인 추정에는 근거와 불확실성을 함께 표시하고 운영 변경 명령으로 실행하지 않는다.

HRD 기능은 특정 프로젝트의 채널 규칙·SQL parser·선택 HANA join을 가진다. 이를 범용 업무 점검에 확장할 때 원래 capability 경계를 유지한다. 읽기 일일 점검에 `send_test_message`를 섞지 않는다.

APP-P09/P10 수용 시험: 동일 Name/다른 Namespace, 반복 module, table null/empty, User/Active 차이, nonempty Party, secret unknown fixture를 보존한다. 다른 업무의 같은 채널명과 다른 scope가 연결되면 실패다. raw payload·원천 credential이 frontend DTO·LLM context·로그·diff에 나타나지 않아야 한다.

## APP 10 P2 개발 자동화 plan-only 프로토타입

### APP 10.1 APP-P11 기존 제품에 추가할 범위

첫 범위는 **명세 입력→DT/MT/SI/MM/OM·Channel/ICO 논리 모델→참조 검증→계획 미리보기→보고서 내보내기**다. SAP 객체 생성·저장·컴파일·활성화·채널 제어를 호출하지 않는다. 실제 원격 작성은 AUT 절의 별도 검증 milestone이다.

후보 구조는 `backend/app/domains/authoring/{router,models,planner,validator,repository}.py`, `backend/app/integrations/sap_po/{directory_authoring,esr_bridge}.py`, 별도 Java worker, `frontend/src/domains/authoring/`다. 이 경로는 현재 없는 설계안이다. 기존 monitoring/channels 도메인 안에 임의 쓰기 URL·class 이름을 받아 실행하는 기능을 넣지 않는다.

UI는 schema version·namespace·SWCV logical reference·송수신 필드 구조·SI operation·단순 필드 매핑·채널 템플릿을 입력받는다. source/target 2DT+2MT+2SI+1MM+1OM의 완전한 graph와 Channel/ICO 계획을 출력한다. unresolved target·중복 logical ID·cycle·불일치 signature를 남긴 계획은 READY로 표시하지 않는다. 존재하는 SAP key/버전/권한은 offline 입력만으로 검증됐다고 표시하지 않는다.

단순 매핑의 첫 capability는 사용자가 지정한 1:1 field assignment와 상수 등 명확한 부분집합이다. arbitrary UDF, multi-mapping, 복잡한 context/queue semantics, 동적 receiver를 자동 지원한다고 주장하지 않는다. 모델 생성과 실제 메시지 변환 실행 성공은 별도다. 필드 의미를 임의로 추론해 업무 규칙을 완성하지 않는다.

Python이 입력 검증·참조 DAG·plan 상태·저장을 맡고 Java worker는 버전 고정 SAP SDK 모델을 맡는 경계가 현 실증과 맞는다. SDK JAR를 frontend bundle이나 이 GitHub 문서에 포함하지 않는다. SDK classpath·runtime SHA는 내부 허용 배포본으로 준비한다. pure Python ESR wire 재구현이나 JPype를 검증된 구현처럼 소개하지 않는다.

개발 DB에는 plan/revision·logical object·ref binding·validation·future execution journal을 구분한다. 아직 실제 server reference가 없으면 null/unresolved로 남긴다. offline logical ID를 server GUID로 위장하지 않는다. GUI용 모든 Java main을 실행하거나 headless 실패를 GUI 자동 클릭으로 해결하려고 하지 않는다.

APP-P11 수용 시험: 정상 1:1 명세, 누락·중복·cycle·타입 불일치·미지원 capability·과도한 크기, manifest revision drift를 검사한다. 동일 입력에 결정적인 계획이 나오고 source/target 참조가 유지돼야 한다. prototype test 전체에서 SAP/DB 운영 원본·network mutation dispatch는 0이어야 한다. 파일 업로드 내용은 지시가 아니라 데이터로 파싱하고 임의 URL·코드·Java class를 실행하지 않는다.

## APP 11 polling 동시성 및 권한을 함께 지키기

현재 대시보드는 15분마다 갱신하고 전용 실시간 메시지는 15초다. 12초 dashboard timeout은 브라우저 요청 대기의 한도이며 SAP collector가 12초 안에 종료됐다는 증거가 아니다. UI timeout 뒤 backend 호출이 남을 수 있으므로 취소·서버 deadline·다음 요청과의 중복을 측정한다.

권장 흐름은 `bounded provider collection → 저장 snapshot → 여러 UI 조회`다. 대시보드 사용자 수에 비례해 SAP 요청 수가 늘지 않도록 한다. source별 polling 간격, timeout, 최대 행/응답 크기, 단일 실행 잠금, 실패 backoff와 manual refresh cooldown을 설정한다. 수집 주기는 현 서버의 부하·응답 시간을 관찰해 정하며 과거 snapshot을 운영 권장 주기로 승격하지 않는다.

모든 새 read route는 `require_permissions + require_server_access + ServerRegistry.require_capability`를 통과한다. 여러 SID를 한 API의 임의 배열로 우회하면 기존 SID 경계를 잃을 수 있다. 저장 snapshot·event를 조회할 때도 resource SID로 필터한다. 캐시 key에는 SID·source·auth scope·query/contract version이 포함돼야 한다. 다른 사용자의 더 넓은 SAP 가시성 결과를 낮은 권한 사용자에게 공유하지 않는다.

기존 `channel-control`, `channels:control`, ADMIN `*`는 authoring 실행 허가와 같은 capability가 아니다. plan/read/execute/activate를 구분하는 새 제품 권한을 설계하더라도 prototype에는 execute/activate dispatch를 구현하지 않는다. HTTP GET/POST 여부만으로 SAP 읽기·쓰기를 판정하지 않고 operation allowlist를 사용한다.

## APP 12 구현 순서와 완료 판정

| 작업 ID | 선행 조건 | 코드 변경 중심 | 종료 조건 |
|---|---|---|---|
| APP-P00 | 현재 checkout·fixture 확보 | 공통 source/신선도/완전성 DTO, 운영 mock 제거 | 모든 실패·샘플·0건 상태가 구분되고 다른 SID 값 오염 없음 |
| APP-P01 | 채널 raw fixture | 상태 decoder, summary·UI, snapshot/event | unknown 정상 오인 없음, started와 health 분리, 부분 누락으로 복구 판정 안 함 |
| APP-P02 | Query raw shape | 전용 inventory parser | 0/1/N·Party·wrapper·거부 건수 일치, 소비 화면 회귀 |
| APP-P03 | 설치 WSDL·MON 계약 | 표준 메시지 provider와 Audit 연결 | Fault/auth/0건·목록·ID·필터 구분, HOST_ID 임의 추정 없음 |
| APP-P04 | P03 또는 기존 RTIMS | bounded 집계·pagination·complete meta | cap·경계·중복·late arrival·scope 검사, 표본을 총건수로 표시 안 함 |
| APP-P05 | MON 세션 계약 | 44 metric provider와 session single-flight | 정의 집합 검사·제한 복구·자격 변경 격리, 자연 만료는 별도 결과 |
| APP-P06 | P00/P05 | 관측 저장·스케줄 조정·lease | 기존 Oracle transaction/checkpoint 보존, 중복 worker 검증 |
| APP-P07 | 현재 alert_event migration 확인 | alert repository·ACK·resource SID ACL | reload 이후 확인 보존, 타 SID 차단, 동시 상태 전이 검사 |
| APP-P08 | P01/P04/P06/P07 | rules·dedup·recovery·UI | stale/partial 입력 오경보 방지와 재발·복구 이력 |
| APP-P09 | P02·typed Read fixture | 비밀 제외 snapshot·설정 diff | 속성 namespace/table/module/context 손실 없음 |
| APP-P10 | 식별자·범위 검증 | 업무 연결·점검·LLM typed context | 근거 있는 연결만 표시, 비밀 비노출, 테스트 전송 없음 |
| APP-P11 | AUT 논리 계약 | offline authoring domain·UI·plan 저장 | 완전한 1:1 계획과 오류 보고서, SAP write dispatch 0 |

각 작업은 서로 다른 증거 상태를 기록한다: `CODE_IMPLEMENTED`, `OFFLINE_TESTED`, `LIVE_READ_VERIFIED`, `SANDBOX_WRITE_VERIFIED`, `NOT_VERIFIED`. 이 이름은 새 상태 설계안이다. 한 단계의 성공을 다음 단계 성공으로 자동 승격하지 않는다. 141개 요구사항 수를 완료율 또는 서버 성공률로 사용하지 않는다.

## APP 13 본사에서 실행할 검증과 기록

아래 명령은 **본사 구현 이후 사용할 절차 예시이며 이번 인계 작성에서 실행하지 않았다.** 본사 보안 정책·Python/runtime 설치 규칙과 대상 checkout을 먼저 확인한다. 기존 `.env`를 출력하거나 운영 credentials로 무심코 실행하지 않는다. offline 시험에는 외부 HTTP/DB를 fake로 대체하고, startup scheduler와 IFS 같은 선택 작업도 꺼야 한다.

```powershell
# PROJECT_ROOT에서 문서 계약 검사. 앱을 기동하는 명령이 아니다.
python --version
python scripts/validate_project_docs.py

# backend 폴더에서. 모든 외부 adapter를 fake로 고정한 테스트만 실행한다.
Set-Location backend
python -m pytest tests/test_sap_po_integration.py tests/test_monitoring_extensions.py tests/test_config.py
python -m pytest tests/test_collector_scheduler.py tests/test_oracle_collector_contract.py
python -m pytest tests/test_dashboard.py tests/test_required_features.py tests/test_llm_provider.py tests/test_certificates.py
```

현재 Oracle 계약 시험에는 가짜 cursor와 별도 opt-in 실DB 시험이 섞일 수 있으므로 테스트 코드와 opt-in 조건을 먼저 읽는다. “테스트”라는 이름만 보고 운영 DB에 연결하지 않는다. 개발 작업 중 새 fixture/test를 추가하고 위 관련 테스트에 포함한다. framework가 `settings`를 import할 때 실제 설정을 읽을 수 있다는 점도 격리한다.

```powershell
# PROJECT_ROOT/frontend에서. package lock의 현 상태와 사내 패키지 공급을 먼저 확인한다.
npm --version
npm run lint
npm test
```

현재 `npm test`는 `npm run build && node --test tests/rendered-html.test.mjs`이며 임시 Next server를 사용하는 검증이다. 단순 정적 검사와 다르다. 외부 API를 mock하고 포트·종료 처리·비밀 비노출을 검사한다. 통과했다는 보고에는 실행한 버전·명령·시각·fixture·종료 코드·미검증 외부 연결을 명시한다. 실제 명령을 실행하지 않았으면 PASS로 쓰지 않는다.

권한 있는 본사 읽기 검증은 별도 단계다. source별 하나의 bounded 조회부터 시작하고 WSDL 원본과 hash, 요청 operation/QName, 응답 shape/원문 건수/변환 건수, 인증 principal 범위, 시간대·단위, cap·warning을 기록한다. 원문 credential·cookie·업무 body는 기록하지 않는다. UI에서 값을 봤다는 사실과 독립 collector가 수집했다는 사실을 구분한다. 인증 실패 때문에 SAP 역할·policy·cache·채널 상태를 자동 변경하지 않는다.

문서 갱신은 실제 변경에 맞춰 domain API/README/MANUAL/SKILL/ERROR, cross-domain ADR·PROJECT·CHANGELOG를 갱신한다. 실패와 unresolved 항목을 지우지 않고 검증한 개선 범위와 함께 남긴다. 원격 서버 mutation과 운영 배포는 현재 작업의 읽기·offline 범위를 넘어서는 별도 실행 계획이다.

## APP 14 본사 에이전트에 붙여넣을 작업 지시문

다음은 본사 에이전트가 해당 환경의 권한과 저장소 규칙을 확인한 뒤 사용할 시작 지시문이다. 아래 문구만으로 SAP 쓰기·배포를 허가하는 것은 아니다.

```text
이 인계 문서의 APP/MON/AUT 절과 원본 증거를 읽고 PO_MONITOR_MAIN을 보완하라.

1. AGENTS.md, PROJECT.md, CURRENT_TASK.md, 대상 영역·도메인 문서부터 읽는다.
   현재 HEAD/branch/dirty 상태와 본사 런타임 계약을 기록하고 기존 변경을 보존한다.
2. 우선 APP-P00/P01/P02를 구현한다. 운영 mock fallback, unknown 정상 판정,
   CommunicationChannel Query 배열 파싱과 source/신선도/완전성 정보를 보완한다.
3. 다음 APP-P03/P04로 검증된 표준 메시지 읽기 provider를 추가한다.
   기존 RTIMS SQL count와 Audit 고정 계약을 유지하고 목록 길이를 전체 count로 표시하지 않는다.
4. APP-P05/P06으로 44개 지표 provider를 분리한다. NWA 로그인과 Basic endpoint를 구분하고
   제한된 재로그인·single-flight·계약 검사를 구현한다. UI마다 SAP session을 새로 만들지 않는다.
   기존 HANA→Oracle buffer/procedure/checkpoint transaction을 변경하지 않는다.
5. APP-P07/P08은 기존 alert_event schema를 확인하고 resource SID ACL·ACK 영속화·중복 억제·복구를 연결한다.
6. APP-P11은 plan-only 프로토타입으로 구현한다. 2DT/2MT/2SI/MM/OM과 Channel/ICO의
   논리 참조·필수값·타입을 검증하고 미리보기/보고서를 제공한다.
   로컬 모델 성공을 SAP 저장·컴파일·활성화 성공으로 표시하지 않는다.
7. 이번 범위에서 SAP 설정/권한/인증 policy/보존/로깅/cache를 변경하지 않는다.
   채널 START/STOP/automation 변경, 메시지 resend/cancel, 테스트 전송,
   실제 객체 create/change/save/activate/delete를 호출하지 않는다. 브라우저 새 탭도 만들지 않는다.
8. 실제 서버에 대한 허용된 읽기 검증은 operation allowlist, bounded row/time/response size,
   계정·SID scope와 secret 비노출을 확인한 뒤 수행한다. 범위가 없으면 offline fixture로 진행한다.
9. 각 작업의 코드 구현, offline 시험, live read, sandbox write 상태를 구분하고
   실행한 검사와 남은 공백을 기록한다. 실행하지 않은 검사를 PASS로 쓰지 않는다.
10. 작업마다 관련 도메인 문서와 오류 이력을 갱신하고 변경 파일만 명시적으로 커밋한다.
```

## APP 15 이 장의 재확인에 사용할 저장소 자료

근거의 기준은 `AGENTS.md`, `PROJECT.md`, `docs/LEGACY_FEATURE_COVERAGE.md`와 각 도메인의 다섯 문서다. 기능 목록은 이 문서의 설명만 믿고 완료 처리하지 말고 실제 코드와 fixture를 함께 읽는다.

- 핵심 코드: `backend/app/domains/{monitoring,channels,messages,alerts,collectors}/`, `backend/app/integrations/sap_po/{client,normalize}.py`, `backend/app/core/{config,security}.py`.
- UI 계약: `frontend/src/domains/dashboard/OperationsWorkspace.tsx`, `frontend/src/domains/messages/RealtimeInterfacesPage.tsx`, `frontend/src/core/{types,api,refresh}.ts`, 관련 domain API 문서.
- 재사용 기능: `backend/app/domains/{interfaces,certificates,hrd,llm_search}/`, `backend/app/domains/channels/bulk_service.py`.
- 저장 구조: `backend/migrations/001_initial.sql`, `002_dashboard_alert_llm.sql`, `004_monitoring_policy_and_iam.sql`, 이후 현재 적용된 migration 목록.
- 회귀 검사: `backend/tests/test_sap_po_integration.py`, `test_monitoring_extensions.py`, `test_config.py`, `test_collector_scheduler.py`, `test_oracle_collector_contract.py`, `test_required_features.py`, `test_llm_provider.py`, `test_certificates.py`, `frontend/tests/rendered-html.test.mjs`.

이 장의 작성 과정은 읽기와 인계 Markdown 작성에 한정했다. 애플리케이션 저장소 수정·새 SAP 호출·기능 구현·실행 검증을 수행한 결과로 해석하지 않는다.

## MON 1 모니터링 조사 결과를 구현에 사용하는 방법

이 장은 2026년 10월 15일과 18일 KST에 수행한 읽기 실증을 바탕으로 한다. 실제 HTTP 호출은 별도 Python client가 수행했고, REA는 안전하게 투영한 HAR와 설치 계약을 해독했다. REA가 SAP 서버 내부 인증 모듈이나 DB 실행을 추적한 결과는 아니다. 현재 본사 서버가 동일한 SP·WSDL·로그온 정책이라는 보장은 없으므로 설치별 계약을 먼저 고정한다.

아래 코드와 DTO는 에이전트가 제품 구현을 시작할 수 있도록 새로 작성한 예시다. 조사 당시 제품 저장소에 통합·배포된 코드가 아니다. `OFFLINE`은 메모리·fixture만 처리하는 예시, `READ_ONLY`는 승인된 대상의 상태·메타데이터를 읽는 HTTP 계약이다. 이 장에는 채널 제어, 메시지 취소·재전송, payload 조회, 캐시 갱신, 작업 실행 코드가 없다.

### MON 1.1 세 원본을 서로 다른 provider로 구현한다

| Provider | 실제 실증한 경로 | 당시 인증 | 반환 결과 | 섞으면 안 되는 의미 |
|---|---|---|---|---|
| AS Java 시스템 지표 | `POST /_tc~monitoring~webservice~web/JEEMONWSService` | NWA form 로그인으로 얻은 자체 세션 CookieJar | 요청 정의 44개에 대응하는 지표 44개 | PO 업무 메시지·채널 상태·Job 전체 지표 44종이 아님 |
| PO 메시지 메타데이터 | `POST /AdapterMessageMonitoring/basic?style=document` | Basic, 첫 호출에 브라우저 Cookie 불필요 | 제한된 조회의 목록·상태·상한/권한 경고 | 응답 `number`가 전역 total이라는 보장 없음 |
| 런타임 채널 상태 | `GET /AdapterFramework/ChannelAdminServlet?action=status&...` | Basic, 첫 호출에 브라우저 Cookie 불필요 | 당시 고유 ChannelID 1,300개 | 모든 AE·모든 노드·모든 권한 범위의 전체 인벤토리 증명은 아님 |

메시지와 채널은 Basic으로 성공했지만 지표 SOAP에서는 Basic 단독 호출이 Guest 문맥의 정상 형태 빈 응답이었다. 따라서 공통 `HTTP 200 => SUCCESS`나 공통 `빈 배열 => 로그인 재시도` 규칙을 만들지 않는다. 인증 전략·성공 계약·빈 결과 해석은 provider별로 둔다.

### MON 1.2 본사에서 준비할 설정

원격 주소는 backend registry의 서버별 origin으로부터 계산한다. 예시 origin은 `https://po.example.invalid:50001`이며 실제 호스트·포트의 대용값이다. 조사 당시 HTTP 사용이 본사 HTTPS 비활성화의 근거가 되지 않는다. TLS는 본사 CA를 신뢰하도록 구성하고 무조건 검증을 끄지 않는다.

| 설정 | 구현 규칙 |
|---|---|
| SID/engine scope | 기존 서버 접근 권한을 재사용하되 서버와 AE 범위를 함께 보존 |
| 자격 증명 | 기존 backend secret 설정에서 주입. CLI 인자·작업 JSON·frontend·Git에 평문 저장 금지 |
| 경로 override | 서버별로 허용된 relative path만 설정. 사용자가 임의 URL을 입력해 실행하게 만들지 않음 |
| WSDL import host alias | 기존 `rewrite_host_alias`의 명시적 hostname allowlist를 유지. 모든 host를 현재 origin으로 치환하지 않음 |
| timeout/size | connect/read timeout·최대 응답 bytes·한 주기 요청 수를 명시. 아래 20초/2MB는 과거 probe의 한도이지 SAP 보장값이 아님 |
| 인증 세션 | 서버·principal·인증 방식별 소유권 분리. browser Cookie 복사·계정 간 jar 공유 금지 |
| 로그 | operation·relative path·시각·HTTP status·오류 분류·개수만 저장. Authorization/Cookie/hidden token/XML 업무 식별값은 제외 |
| 실행 분류 | 전송은 POST여도 SOAP read operation이면 읽기로 분류. HTTP verb만으로 쓰기/읽기를 결정하지 않음 |

## MON 2 AS Java 44개 지표의 정확한 요청 계약

### MON 2.1 HTTP와 QName

`READ_ONLY` 계약:

```http
POST /_tc~monitoring~webservice~web/JEEMONWSService
Content-Type: text/xml; charset="UTF-8"
```

과거 독립 collector는 이 호출에 Basic Authorization을 보내지 않고 자신의 CookieJar를 사용했다. `SOAPAction` 헤더는 명시적으로 구성하지 않은 상태로 정상 수집됐다. 이를 다른 설치의 WSDL SOAPAction 값으로 일반화하지 않는다. 본사 설치의 binding이 헤더를 요구하면 원본 WSDL/정상 요청을 확인하고 별도 profile에 고정한다.

| 항목 | 검증한 형태 |
|---|---|
| Envelope namespace | `http://schemas.xmlsoap.org/soap/envelope/` (SOAP 1.1) |
| operation QName | `{http://sap.com/monitoring/ws/}retrieveMonitors` |
| 반복 인자 | operation 바로 아래의 **namespace 없는** `monitors` |
| 각 정의의 자식 순서 | `aggregationType`, `monitorName`, `monitorPath`, `monitorType`, `textMonitorName` |
| 성공 wrapper QName | `{http://sap.com/monitoring/ws/}retrieveMonitorsResponse` |
| 응답 항목 | wrapper 바로 아래 namespace 없는 `return` |
| 응답 필드 | `aggregationType`, `monitorName`, `monitorType`, `monitorValue`, `state`, `textMonitorName` |

`monitorPath`의 `\`, 공백, 대소문자, `%s`·`%l` 표시는 정의의 일부다. Python `%` formatting이나 URI encoding을 적용하지 않는다. XML 텍스트이므로 XML serializer가 필요한 escaping만 수행한다. 특히 평균 CPU path의 `CPUCPU_Utilization`은 관측된 요청 자체의 값이며 개발자가 임의로 고치지 않는다.

### MON 2.2 전체 44개 정의

다음 표는 요청 XML과 CSV를 대조한 전체 정의다. `agg`와 `type`은 요청의 숫자 코드다. `agg=1/2/3/4`를 sum/max/average 등으로 전역 매핑하는 공식 의미는 이번 조사로 확정하지 않았다. 동일 `monitorName`을 여러 path·aggregation으로 조회하므로 `monitorName` 하나를 primary key로 사용하면 안 된다.

| # | 요청 textMonitorName | 응답 label (다를 때만) | monitorName | monitorPath | agg | type |
|---:|---|---|---|---|---:|---:|
| 1 | `httpRequestsFrequency` | 동일 | `HTTP.RequestsFrequency` | `\Services\Http Provider\General\Requests frequency` | 1 | 2 |
| 2 | `jsfJ2eeSessionsNumBrw` | 동일 | `JSF_J2EESessions_Num_Brw` | `\Sessions AS Java\Browser Sessions` | 1 | 3 |
| 3 | `logCfgNumberOfErrorLogs` | 동일 | `LOG_CFG.NumberOfErrorLogs` | `\Services\Log Configurator\Messages\Error` | 1 | 2 |
| 4 | `sessMgmtActiveWebSessionCount` | 동일 | `SessMgmt.ActiveWebSessionCount` | `\Kernel\Session Manager\Active Web Sessions Count` | 1 | 2 |
| 5 | `sessMgmtOpenWebSessionCount` | 동일 | `SessMgmt.OpenWebSessionCount` | `\Kernel\Session Manager\Opened Web Sessions Count` | 1 | 2 |
| 6 | `webAverageProcessingTime` | 동일 | `WEB.AverageProcessingTime` | `\Services\Web Container\AverageProcessingTime` | 3 | 2 |
| 7 | `cpuUtilizationAverage` | 동일 | `CPU_Utilization` | `\OperatingSystem\CPUCPU_Utilization` | 3 | 1 |
| 8 | `logCfgNumberOfFatalLogs` | 동일 | `LOG_CFG.NumberOfFatalLogs` | `\Services\Log Configurator\Messages\Fatal` | 1 | 2 |
| 9 | `licenseMgrLicenseValidPeriod` | 동일 | `LicenseMgr.LicenseValidPeriod` | `\Kernel\Licensing Manager\License Validity Period\J2EE-Engine_%l` | 2 | 2 |
| 10 | `icmGeneralQueuelenGroup` | 동일 | `ICM_GENERAL_QUEUELEN_GROUP` | `\R3Services\ICM\General\QueueLen` | 2 | 1 |
| 11 | `systemEntryExpirationPeriod` | 동일 | `SYSTEM.ENTRY.EXPIRATION.PERIOD` | `\Services\Keystore\DaysToExpire` | 2 | 2 |
| 12 | `threadMgrWaitTasksQueOverflow` | 동일 | `ThreadMgr.WaitTasksQueOverflow` | `\Kernel\System Threads Pool\Waiting Tasks Queue Overflow` | 3 | 2 |
| 13 | `heapFileNumber` | 동일 | `HeapFileNumber` | `\Performance\Out Of Memory\Heapdump file number` | 1 | 2 |
| 14 | `deployFailedToStart` | 동일 | `DEPLOY.FailedToStart` | `\Services\Deploy\Common Information\Failed To Start Applications` | 2 | 2 |
| 15 | `failedToStartServices` | 동일 | `FailedToStartServices` | `\Kernel\Services\Failed to start services` | 2 | 2 |
| 16 | `logCfgLogsPerMin` | 동일 | `LOG_CFG.LogsPerMin` | `\Services\Log Configurator\Messages\Log frequency` | 3 | 2 |
| 17 | `memoryUtilizationGroupAverage` | 동일 | `MemoryUtilizationGroup` | `\Performance\System\Memory Utilization` | 3 | 2 |
| 18 | `memoryUtilizationGroupMax` | 동일 | `MemoryUtilizationGroup` | `\Performance\System\Memory Utilization` | 2 | 2 |
| 19 | `conSapackRaNameTocrps` | 동일 | `Con.SA.pack.raName.TOCRPS` | `\Services\Connector Service\Stand Alone\javax.sql.DataSource\SAP%sDB\TimedOutConnectionRequestsPerSecond` | 1 | 2 |
| 20 | `conSapackRaNameMcur` | 동일 | `Con.SA.pack.raName.MCUR` | `\Services\Connector Service\Stand Alone\javax.sql.DataSource\SAP%sDB\ManagedConnectionsUsageRate` | 2 | 2 |
| 21 | `extCommAverageExternalRfcTime` | 동일 | `EXT_COMM.AverageExternalTime` | `\Performance\External Communication\Average RFC Time` | 3 | 2 |
| 22 | `getFreeDiskSpace` | 동일 | `getFreeDiskSpace` | `\Performance\System\Free Disk Space` | 4 | 2 |
| 23 | `extCommAverageExternalWebServiceTime` | 동일 | `EXT_COMM.AverageExternalTime` | `\Performance\External Communication\Average WebService Time` | 3 | 2 |
| 24 | `extCommAverageRfcIO` | 동일 | `EXT_COMM.AverageIO` | `\Performance\External Communication\Average RFC IO` | 3 | 2 |
| 25 | `extCommAverageWebServiceIO` | 동일 | `EXT_COMM.AverageIO` | `\Performance\External Communication\Average WebService IO` | 3 | 2 |
| 26 | `extCommNumberOfWebServiceCalls` | 동일 | `EXT_COMM.NumberOfCalls` | `\Performance\External Communication\External WebService Calls` | 3 | 2 |
| 27 | `extCommNumberOfRfcCalls` | 동일 | `EXT_COMM.NumberOfCalls` | `\Performance\External Communication\External RFC Calls` | 3 | 2 |
| 28 | `conSaPackRaNameWmcc` | 동일 | `Con.SA.pack.raName.WMCC` | `\Services\Connector Service\Stand Alone\javax.sql.DataSource\SAP%sDB\WaitingForManagedConnectionCount` | 1 | 2 |
| 29 | `jsfJavaMemoryLocalObjectsRatioMax` | 동일 | `JSF_JavaMemory_LocalObjects_Ratio` | `\Java Heap Memory\Memory of %s\Utilization Local Objects` | 2 | 3 |
| 30 | `jsfJavaMemoryLocalObjectsRatioAverage` | 동일 | `JSF_JavaMemory_LocalObjects_Ratio` | `\Java Heap Memory\Memory of %s\Utilization Local Objects` | 3 | 3 |
| 31 | `jsfProcessNumRestarts` | 동일 | `JSF_Process_NumRestarts` | `\Process Table\%s\Number of Restarts` | 1 | 3 |
| 32 | `jsfThreadsNumLongrunners` | 동일 | `JSF_Threads_Num_Longrunners` | `\Threads\Threads of %s\Long Running Threads` | 1 | 3 |
| 33 | `cpuUtilizationMax` | 동일 | `CPU_Utilization` | `\OperatingSystem\CPU\CPU_Utilization` | 2 | 1 |
| 34 | `jsfGarbageCollDurationFullGC` | 동일 | `JSF_GarbageColl_Duration_Full_GC` | `\Garbage Collection\GC of %s\Duration of Last Full GC` | 2 | 3 |
| 35 | `jsfGarbageCollCollectedMemory` | 동일 | `JSF_GarbageColl_CollectedMemory` | `\Garbage Collection\GC of %s\Released Memory per Minute` | 2 | 3 |
| 36 | `pageIn` | 동일 | `Page_In` | `\OperatingSystem\Paging\Page_In` | 1 | 1 |
| 37 | `pageOut` | 동일 | `Page_Out` | `\OperatingSystem\Paging\Page_Out` | 1 | 1 |
| 38 | `jsfGarbageCollAvgDuration` | 동일 | `JSF_GarbageColl_AvgDuration` | `\Garbage Collection\GC of %s\Average Proportion of Total Time` | 2 | 3 |
| 39 | `jsfProcessStatusStartedNodes` | `StartedNodes` | `JSF_Process_Status` | `\Process Table\%s\Process Status` | 1 | 3 |
| 40 | `jsfProcessStatusFailedNodes` | `FailedNodes` | `JSF_Process_Status` | `\Process Table\%s\Process Status` | 1 | 3 |
| 41 | `jsfInstanceNumServerNodes` | 동일 | `JSF_Instance_numServerNodes` | `\General Instance Information\Number of Server Nodes` | 1 | 3 |
| 42 | `webError500Count` | 동일 | `WEB.Error500Count` | `\Services\Web Container\Error500Count` | 1 | 2 |
| 43 | `getGCProblems` | 동일 | `getGCProblems` | `\Kernel\SAPJVM\GCProblemReporting\GC Problems` | 2 | 2 |
| 44 | `getSystemProblems` | 동일 | `getSystemProblems` | `\Kernel\SAPJVM\SystemProblemReporting\System Problems` | 2 | 2 |

44개는 고유 요청 `textMonitorName` 기준이고 `monitorName`의 고유 값은 37개다. 요청 `jsfProcessStatusStartedNodes`와 `jsfProcessStatusFailedNodes`는 응답 `StartedNodes`·`FailedNodes`로 돌아왔다. 이 두 alias만 명시적으로 적용한다. 대소문자 무시·접두사 제거 같은 추측성 정규화는 하지 않는다.

### MON 2.3 OFFLINE 요청 생성 예시

`definitions`에는 위 표의 44개 행을 다음 필드명으로 변환한 버전 고정 설정을 전달한다. CSV를 사용할 경우 `requestTextMonitorName`, `monitorName`, `monitorPath`, `requestAggregationType`, `requestMonitorType` 열을 보존한다. 실제 비밀값이나 서버 주소를 지표 설정 파일에 넣을 필요는 없다.

```python
# OFFLINE: XML bytes를 만드는 순수 함수. HTTP 요청을 보내지 않는다.
import xml.etree.ElementTree as ET

SOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"
METRICS_NS = "http://sap.com/monitoring/ws/"

def make_metric_request(definitions: list[dict[str, str]]) -> bytes:
    if len(definitions) != 44:
        raise ValueError("expected_exactly_44_metric_definitions")
    labels = [d["requestTextMonitorName"] for d in definitions]
    if len(set(labels)) != 44:
        raise ValueError("duplicate_metric_definition")
    env = ET.Element(f"{{{SOAP11}}}Envelope")
    body = ET.SubElement(env, f"{{{SOAP11}}}Body")
    op = ET.SubElement(body, f"{{{METRICS_NS}}}retrieveMonitors")
    fields = (
        ("aggregationType", "requestAggregationType"),
        ("monitorName", "monitorName"),
        ("monitorPath", "monitorPath"),
        ("monitorType", "requestMonitorType"),
        ("textMonitorName", "requestTextMonitorName"),
    )
    for definition in definitions:
        item = ET.SubElement(op, "monitors")  # unqualified
        for xml_name, key in fields:
            ET.SubElement(item, xml_name).text = str(definition[key])
    return ET.tostring(env, encoding="utf-8", xml_declaration=True)
```

namespace prefix 자체는 `ns1`·`ns0` 어느 것이어도 QName이 같으면 된다. `monitors` 자식까지 기본 namespace를 상속시키는 XML은 이 예시와 다르다. 테스트는 문자열 prefix 비교가 아니라 QName·순서·44개 정의의 동등성을 검사한다.

### MON 2.4 OFFLINE 응답 검사 예시

아래는 관측한 UTF-8 SOAP 1.1 계약을 엄격하게 검사하는 독립 예시다. 제품에서는 기존 hardened XML parser와 응답 제한을 재사용한다. 새 인코딩·새 wrapper는 자동 정상 처리하지 말고 계약 변화로 기록한다.

```python
# OFFLINE: 이미 받은 XML bytes를 검사한다. 로그인/HTTP/파일 저장을 하지 않는다.
from decimal import Decimal, InvalidOperation
import xml.etree.ElementTree as ET

SOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"
METRICS_NS = "http://sap.com/monitoring/ws/"
ALIASES = {
    "StartedNodes": "jsfProcessStatusStartedNodes",
    "FailedNodes": "jsfProcessStatusFailedNodes",
}

def parse_bounded_utf8_xml(data: bytes, max_bytes: int) -> ET.Element:
    if not data or len(data) > max_bytes or b"\x00" in data:
        raise ValueError("xml_size_or_encoding_rejected")
    text = data.decode("utf-8-sig", errors="strict")
    upper = text.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise ValueError("xml_dtd_or_entity_rejected")
    return ET.fromstring(text)

def parse_metrics(data: bytes, definitions: list[dict[str, str]]) -> dict:
    root = parse_bounded_utf8_xml(data, max_bytes=2_000_000)
    if root.tag != f"{{{SOAP11}}}Envelope":
        raise ValueError("unexpected_soap_envelope")
    body = root.find(f"{{{SOAP11}}}Body")
    if body is None:
        raise ValueError("soap_body_missing")
    if body.find(f"{{{SOAP11}}}Fault") is not None:
        raise ValueError("soap_fault")
    response = body.find(f"{{{METRICS_NS}}}retrieveMonitorsResponse")
    if response is None:
        raise ValueError("metric_wrapper_missing")
    expected = {d["requestTextMonitorName"]: d for d in definitions}
    rows = response.findall("return")
    if len(rows) == 0:
        return {"status": "EMPTY_REQUIRED_METRICS", "items": []}
    if len(expected) != 44 or len(rows) != 44:
        raise ValueError("partial_or_excess_metrics")
    found = {}
    allowed = {
        "aggregationType", "monitorName", "monitorType", "monitorValue",
        "state", "textMonitorName",
    }
    for row in rows:
        keys = [child.tag for child in row]
        if len(keys) != len(set(keys)) or set(keys) != allowed:
            raise ValueError("metric_fields_changed")
        raw = {child.tag: child.text or "" for child in row}
        label = ALIASES.get(raw["textMonitorName"], raw["textMonitorName"])
        if label not in expected or label in found:
            raise ValueError("unknown_or_duplicate_metric")
        definition = expected[label]
        if raw["monitorName"] != definition["monitorName"]:
            raise ValueError("metric_name_mismatch")
        if raw["aggregationType"] != str(definition["requestAggregationType"]):
            raise ValueError("metric_aggregation_mismatch")
        try:
            value = Decimal(raw["monitorValue"])
        except InvalidOperation as exc:
            raise ValueError("metric_value_not_numeric") from exc
        if not value.is_finite():
            raise ValueError("metric_value_not_finite")
        found[label] = {**raw, "canonical_label": label}
    if set(found) != set(expected):
        raise ValueError("metric_set_mismatch")
    return {"status": "COLLECTED", "items": list(found.values())}
```

호출자는 위 parser 앞에서 HTTP status·content type·redirect 결과를 검사한다. HTML 로그인 페이지를 XML 0건으로 변환하지 않는다. `state`와 `monitorType`은 원문으로 보존한다. 응답 `monitorType=0`은 요청의 `1/2/3`과 달랐으므로 같은 값임을 성공 조건으로 만들지 않는다. 지표 수신 성공과 지표가 나타내는 시스템 health 정상 여부도 별도다.

### MON 2.5 단위·표시·알람

- 관측된 UI 변환 중 `httpRequestsFrequency`와 `logCfgLogsPerMin` 두 값에만 `ceil(raw/100)` 적용 근거가 있었다. 다른 42개에 같은 배율을 적용하지 않는다.
- `raw_monitor_value`, `raw_state`, `request_aggregation_type`, `request_monitor_type`, `response_monitor_type`, `definition_version`을 저장한다. 단위·scale 미확정은 `null` 또는 `unverified`로 유지한다.
- `SYSTEM.ENTRY.EXPIRATION.PERIOD`는 System Overview의 집계 지표다. 이 값 하나로 특정 Keystore Alias별 인증서 만료일을 만들어내지 않는다.
- 평균·최대라는 요청 label은 원 UI의 선택을 설명하지만 노드 집계 방식·분모·시간 구간까지 입증하지 않는다. 특히 CPU 평균 path와 CPU 최대 path가 다르다.
- heap dump 개수·문제 보고 수치가 0이 아니라고 자동 장애 확정하지 않는다. state의 일반 enum 사전·지표별 threshold·보관 구간을 본사 화면과 대조한 뒤 알람 정책을 별도 등록한다.

## MON 3 NWA 자동 로그인과 세션 복구

### MON 3.1 왜 Basic 단독을 모든 SOAP에 적용하면 안 되는가

과거 지표 SOAP의 동일 요청 XML에 대해 Basic 명시 요청과 무인증 요청은 HTTP 200·368-byte 정상 형태 빈 응답으로 같았다. 서버 Incoming Calls에서 해당 시각·경로가 Guest로 기록된 반면 정상 browser poll은 로그인 사용자 문맥이었다. 대상 앱에 BasicPasswordLoginModule 구성이 있다는 사실도 확인했으나 특정 SOAP 자원 요청에서 그 모듈이 실제 사용자 문맥을 만들었다는 증거는 아니다. 내부 모듈 분기 원인은 확정하지 않았다.

따라서 역할을 임의로 추가하거나 로그인 정책을 바꾸는 해결책을 넣지 않는다. 본사 설치의 Basic 성공 여부를 먼저 읽기 대조하고, 같은 증상이라면 아래 세션 방식의 별도 provider를 사용한다. 메시지 SOAP와 채널 servlet까지 NWA 세션으로 강제 통일하지 않는다.

### MON 3.2 READ_ONLY 로그인 순서

1. 서버·계정별 빈 CookieJar를 생성한다. 브라우저 쿠키를 가져오지 않는다.
2. 정상 진입점 `GET /nwa`를 요청한다. redirect는 같은 configured origin과 승인한 NWA/UME 경로만 허용한다. 관찰한 path 계열은 `/webdynpro/resources/sap.com/tc~lm~itsam~ui~mainframe~wd/`와 `/webdynpro/resources/sap.com/tc~sec~ume~logon~ui/`다. 본사에서 별도 SSO origin을 쓰면 허용 목록을 명시적으로 검토한다.
3. 실제 응답 HTML을 메모리에서 파싱한다. password input이 있는 form이 정확히 하나인지, method가 POST인지 검사한다. form이 없다고 임의의 `j_security_check` URL을 합성하지 않는다.
4. 실제 form의 `action`을 최종 응답 URL 기준 `urljoin`으로 해석하고 origin/path 허용 범위를 다시 검사한다. hidden input 이름·값을 그대로 보존하고 현재 응답의 token만 사용한다.
5. 발견한 username input과 password input에 backend secret을 넣는다. 과거 prototype은 이름이 `j_username`·`sap-user`·`username` 중 하나인 사용자 input을 요구했다. 해당 서버가 다른 이름이면 form adapter를 명시적으로 추가하며 빈 username 추측 전송을 하지 않는다.
6. 필요한 submit input이 `uidPasswordLogon`이면 form에 있는 값을 함께 보낸다. `application/x-www-form-urlencoded`로 전송한다. 실제 과거 form action은 `j_security_check` 계열이었지만 hardcode의 근거로 쓰지 않는다.
7. 같은 CookieJar로 지표 SOAP를 호출한다. password form이 사라졌다는 사실만으로 로그인 완료를 판정하지 않는다. **정확한 44개 응답 검사 통과**가 이 provider의 수집 성공 조건이다.
8. 다음 poll은 jar를 재사용한다. 매 poll마다 새 로그인을 하지 않는다. account/server마다 직렬화된 login singleflight를 두어 병렬 요청이 재로그인을 폭주시키지 않게 한다.

Cookie Domain/Path/Secure 처리는 표준 jar에 맡긴다. JSESSIONID·MYSAPSSO2 등의 값을 직접 문자열로 조합하거나 로그에 남기지 않는다. hidden token·로그인 HTML·비밀번호 form을 fixture로 Git에 저장하지 않는다. UI 애플리케이션 세션 한도와 HTTP 보안 세션은 같은 개념이 아니므로 반복 NWA 앱 진입을 피한다.

### MON 3.3 실제 검증 범위와 미검증 분기

| 단계 | 과거 결과 | 제품에서의 상태 |
|---|---|---|
| 최초 독립 로그인 | 빈 jar → form login → 44개 수신 | 실증됨, 본사 설치 재확인 필요 |
| 같은 jar 재수집 | 추가 로그인 없이 44개 | 실증됨 |
| 로컬 CookieJar 비우기 | 다음 지표 SOAP가 HTTP 200·0개 | 인증 상실 주입의 관측 결과 |
| 수집 함수 내부 복구 | 빈 required set 감지 → 로그인 1회 → SOAP 재시도 1회 → 44개 | 실증됨 |
| 328.721초 무통신 | 같은 jar에서 44개, 비밀번호 로그인 추가 없음 | 관측됨. 동일 서버 세션 ID 생존·SSO 복원 여부는 구분 안 됨 |
| 자연 idle/security/SSO 만료 | 실제 만료 관측 없음 | **미검증** |
| 401/403·잘못된 비밀번호·HTML 로그인·Fault·부분44·통신 장애 | prototype 분기 일부 존재, 해당 라이브 장애 주입 없음 | **추가 구현·시험 필요** |
| password form 없는 SSO 복원 | prototype 별도 처리 없음 | **추가 설계·시험 필요** |

과거 prototype은 요청 timeout 20초·응답 2,000,000 bytes·프로세스 내 로그인 POST 최대 3회·한 collect 안의 복구 SOAP 재시도 1회를 사용했다. 로그인 3회 한도는 재시작 간 전역 제한이 아니다. 운영판에서는 account/server별 로그인 실패 횟수·cooldown을 durable하게 관리하고 잘못된 비밀번호·권한 거부에 무한 재로그인하지 않는다. 관측된 0.325초 복구 시간은 표본 한 건이며 성능 목표로 복사하지 않는다.

### MON 3.4 구현할 상태 전이

다음 상태명은 제품 제안이며 SAP 원문 enum이 아니다.

```text
READY -> READ_METRICS
  exact44                         -> COLLECTED
  normal SOAP + 0 required metrics -> AUTH_SUSPECT -> LOGIN_ONCE -> READ_ONCE
  partial44/duplicate/value error  -> CONTRACT_OR_PARTIAL_ERROR
  HTML/password form              -> AUTH_SUSPECT (bounded recovery)
  401                             -> AUTH_REQUIRED (bounded recovery)
  403                             -> AUTH_OR_PERMISSION_ERROR (분리 확인, 반복 금지)
  SOAP Fault                      -> SOAP_FAULT (내용을 분류, 자동 로그인 만능 처리 금지)
  timeout/network                 -> TRANSPORT_ERROR (별도 bounded read retry)
  login 실패/재수집 실패           -> FAILED 또는 AUTH_REQUIRED + cooldown
```

마지막 정상값은 보존하되 `last_success_at`·`current_collection_status`·`stale`을 함께 내려준다. 실패했다고 기존 44개를 전부 0으로 덮어쓰지 않는다. 자연 만료 검증은 jar를 유지한 무통신 구간·인증 상실/SSO 복원·실제 로그인 횟수·44개 복구를 구분해 새로 기록한다.

## MON 4 표준 SOAP 메시지 메타데이터 수집

### MON 4.1 READ_ONLY endpoint와 설치 계약

```http
POST /AdapterMessageMonitoring/basic?style=document
Content-Type: text/xml; charset=UTF-8
SOAPAction: ""
```

Basic 자격 증명은 HTTP client가 backend 메모리에서 구성한다. 첫 실증 요청은 Cookie 없이 성공했고 이후 자체 load-balancer affinity Cookie만 재사용했다. `/basic` binding은 조사 당시 성공한 경로다. 본사에서 `/ssl`·client certificate binding을 사용할 때는 실제 설치 WSDL과 보안 정책을 따르며 인증 방식을 임의 downgrade하지 않는다.

설치 WSDL을 읽은 경로는 다음과 같다. 모두 GET이며 write operation이 아니다.

```text
/AdapterMessageMonitoring/basic?wsdl&mode=ws_policy&style=document
/AdapterMessageMonitoring/basic?wsdl=binding&style=document&mode=ws_policy
/AdapterMessageMonitoring/basic?wsdl=interface&style=document&mode=ws_policy
```

첫 문서는 service wrapper이고 binding/interface를 import한다. wrapper에서 operation이 보이지 않는다고 API 부재로 결론 내리지 않는다. 본사 원본 WSDL의 import를 동일한 승인 host alias 규칙으로 해결하고 해시를 고정한다. 보존된 `*.redacted.xml`은 xmlns 선언이 QName-valued attribute에서 손실됐을 수 있는 검토 snapshot이므로 executable proxy 생성 입력으로 사용하지 않는다.

| 요소 | 검증한 QName/구조 |
|---|---|
| operation | `{urn:AdapterMessageMonitoringVi}getMessageList` |
| 인자 | 같은 operation namespace의 `filter`, `maxMessages` 순서 |
| filter type/field namespace | `urn:com.sap.aii.mdt.server.adapterframework.ws` |
| response wrapper | `{urn:AdapterMessageMonitoringVi}getMessageListResponse` |
| response member | `{urn:AdapterMessageMonitoringVi}Response` |
| response type fields | 다른 filter/type namespace의 `date?`, `list?`, `number`, `warning`, `displayPermissionWarning` |
| 목록 항목 | `list/AdapterFrameworkData`, 0..unbounded |
| binding | SOAP 1.1 literal, `soapAction=""` |

당시 설치 portType은 operation 24개였고 별도 count operation은 없었다. 같은 서비스에 변경 operation이 존재한다는 이유로 generic method dispatcher를 노출하지 않는다. 이 provider는 `getMessageList`만 allowlist에 두고 기존 Audit 연계는 기존 별도 읽기 adapter로 유지한다.

### MON 4.2 최소 필터와 순서

관측한 공통 필드는 `archive=false`, `dateType=0`, `nodeId=0`, `onlyFaultyMessages=false`, `retries=0`, `retryInterval=0`, `timesFailed=0`, `wasEdited=false`다. 이 숫자가 모든 노드·모든 시간 의미·모든 상태를 자동 포함한다는 문서화는 확보하지 못했다. 받아들여지는 값과 의미가 입증된 값은 다르다.

XSD sequence 전체를 구현할 때는 다음 순서를 유지한다. `?`는 optional, 없는 필드는 생략하고 빈 객체·문자열·nil을 섞지 않는다.

```text
applicationComponent?, archive, connectionName?, correlationID?, dateType,
direction?, errorCategory?, errorCode?, fromTime?, interface?, messageFormat?,
messageIDs?, messageType?, nodeId, onlyFaultyMessages, persistUntil?, protocol?,
qualityOfService?, receiverInterface?, receiverName?, receiverParty?, referenceIDs?,
retries, retryInterval, scheduleTime?, senderInterface?, senderName?, senderParty?,
sequenceID?, serializationContext?, serviceDefinition?, softwareComponent?,
status?, statuses?, timesFailed, toTime?, transport?, validUntil?, wasEdited,
scenarioIDs?, rootID?, returnLogLocations?, onlyLogLocationsWithPayload?
```

초기 구현은 실제 검증한 최소 필터와 제한된 selector만 지원한다. `returnLogLocations`나 payload 관련 selector를 자동 활성화하지 않는다. 사용자별 권한·업무 식별자 노출 범위를 현재 API와 동일하게 검사한다.

### MON 4.3 OFFLINE 요청 XML 생성 예시

```python
# OFFLINE: SOAP bytes만 생성한다. 실제 호출은 별도 READ_ONLY adapter가 수행한다.
from datetime import datetime
import xml.etree.ElementTree as ET

SOAP11 = "http://schemas.xmlsoap.org/soap/envelope/"
MSG_NS = "urn:AdapterMessageMonitoringVi"
FILTER_NS = "urn:com.sap.aii.mdt.server.adapterframework.ws"

def make_message_request(start: datetime, end: datetime, cap: int,
                         status: str | None = None) -> bytes:
    if start.utcoffset() is None or end.utcoffset() is None or start >= end:
        raise ValueError("explicit_timezone_and_increasing_window_required")
    if cap < 1:
        raise ValueError("positive_cap_required")
    # 제품은 endpoint별 maximum cap/maximum window도 별도로 검사한다.
    env = ET.Element(f"{{{SOAP11}}}Envelope")
    body = ET.SubElement(env, f"{{{SOAP11}}}Body")
    op = ET.SubElement(body, f"{{{MSG_NS}}}getMessageList")
    filt = ET.SubElement(op, f"{{{MSG_NS}}}filter")
    ordered = [
        ("archive", "false"), ("dateType", "0"),
        ("fromTime", start.isoformat()), ("nodeId", "0"),
        ("onlyFaultyMessages", "false"), ("retries", "0"),
        ("retryInterval", "0"),
    ]
    if status is not None:
        # status 문자열의 설치 지원 범위는 별도 validation fixture로 고정한다.
        ordered.append(("status", status))
    ordered.extend([
        ("timesFailed", "0"), ("toTime", end.isoformat()),
        ("wasEdited", "false"),
    ])
    for key, value in ordered:
        ET.SubElement(filt, f"{{{FILTER_NS}}}{key}").text = value
    ET.SubElement(op, f"{{{MSG_NS}}}maxMessages").text = str(cap)
    return ET.tostring(env, encoding="utf-8", xml_declaration=True)
```

Python dict→XML 문자열을 일반 정렬하면 XSD sequence가 바뀔 수 있다. 모든 문자열은 serializer로 넣고 XML fragment를 그대로 붙이지 않는다. `maxMessages`가 optional/nillable인 계약이라도 모니터링 수집기는 명시적 양수 상한을 요구한다.

### MON 4.4 응답 파싱과 저장할 최소 필드

QName 경로는 다음과 같다. XML prefix는 고정하지 않는다.

```text
{SOAP11}Envelope/{SOAP11}Body/
  {urn:AdapterMessageMonitoringVi}getMessageListResponse/
  {urn:AdapterMessageMonitoringVi}Response/
    {urn:com.sap.aii.mdt.server.adapterframework.ws}list/
      {urn:com.sap.aii.mdt.server.adapterframework.ws}AdapterFrameworkData
```

반드시 읽을 response metadata는 `number`, `warning`, `displayPermissionWarning`이다. XSD boolean은 `true/false/1/0`을 구분해서 파싱하고 `bool("false")`를 쓰지 않는다. `list` 부재·nil·빈 list와 number=0의 정합도 확인한다. `number`와 목록 길이가 다르거나 필수 flag가 없으면 계약/완전성 오류로 남긴다. 문헌에 없는 `totalCount`, `hasMore`, `offset`을 응답에 만들어 SAP 원문처럼 표시하지 않는다.

| 레코드 필드 | 보존·표시 규칙 |
|---|---|
| `messageKey`, `messageID` | backend 내부 식별·Audit 연계에 사용. 외부 로그·공개 fixture에는 가짜값 또는 일관된 익명화값 |
| `direction`, `status`, `version`, `nodeId` | raw 값 보존. nodeId=0 요청의 전 노드 의미를 추정하지 않음 |
| `startTime`, `endTime`, `scheduleTime` | offset을 유지해 UTC 저장/사용자 시간대로 표시. 서로 다른 timestamp의 의미를 섞지 않음 |
| `senderInterface`, `receiverInterface`, `interface` | namespace/name을 typed 구조로 보존. 문자열 하나만으로 전역 업무 key 생성 금지 |
| `senderName`, `receiverName`, parties | 권한 있는 상세 화면에 필요한 최소값만. 공개 자료로 내보내지 않음 |
| `errorCategory`, `errorCode`, `errorLabel` | 상태와 분리. 알려지지 않은 값은 unknown 원문 |
| `qualityOfService`, `isPersistent`, `retries`, `timesFailed` | 전달 의미/수집 범위 분석용. 단순히 행 개수=업무 실행 수로 환산하지 않음 |
| `duration`, `size` | duration은 구조체일 수 있으므로 XSD의 하위 구조·단위를 먼저 확인. 숫자처럼 flatten 금지 |
| `headers`, `credential`, `endpoint`, `passport`, `passportTID`, log locations | 초기 수집/로그/LLM 문맥에서 기본 제외. 임의 저장으로 비밀·내부 연결정보를 퍼뜨리지 않음 |

`messageKey`만으로 모든 서버·엔진·버전의 전역 유일성이 입증된 것은 아니다. 초기 식별자는 최소 SID+provider/AE scope+원형 messageKey를 포함하고, version/direction 재발행의 충돌을 fixture로 대조한다. GUID인 messageID만 사용해 버전 행을 무조건 합치지 않는다.

### MON 4.5 실증 결과와 집계 알고리즘의 제한

당시 같은 넓은 고정 구간에서 cap=1/10/100은 목록 길이와 `number`가 각각 1/10/16이었다. cap에 도달한 1·10은 warning=true였고 16은 warning=false였다. 제한된 1분 구간은 cap=10과 100 모두 같은 1개였으며, 다른 인증된 구간은 정상 0개였다. 무인증 대조는 HTTP 401·Basic challenge·SOAP Fault였다.

무필터 16개는 raw status canceled 12개·logVersion 4개였다. canceled 필터는 해당 12개와 key 집합이 일치했다. 반면 status=logVersion은 혼합 16개를 그대로 반환해 필터 적용을 입증하지 못했다. 이 16개를 canceled 12개에 더하면 중복이다. logVersion을 정상/오류/업무 건수에서 어떻게 다룰지는 별도 제품 정책이다.

운영 집계는 다음 단계를 구현하되 이 전체 알고리즘이 과거에 실서버 검증됐다고 표시하지 않는다.

1. UTC offset을 포함한 고정 start/end와 동일 필터를 실행 계획에 고정한다. 조회 중 `now()`를 계속 바꾸지 않는다.
2. bounded cap과 bounded window를 사용한다. `warning=true`, 권한 경고, cap 도달이면 완료 집계로 확정하지 않는다.
3. 상한에 걸린 구간을 분할한다. 최소 분할 폭·한 실행 최대 요청 수·총 시간·전체 행 제한에 도달하면 `partial`로 종료한다. 무한 재귀나 전체 보존 이력 스캔을 만들지 않는다.
4. 시간 경계 포함/배제가 미검증이므로 overlap과 dedup 정책을 설치 fixture로 검증한다. 같은 timestamp에 cap보다 많은 행이 몰리면 분할만으로 해결되지 않을 수 있다. 지원되는 더 좁은 selector나 partial 종료가 필요하다.
5. 원형 key와 scope를 보존하며 구간 간 중복을 제거한다. 방향·status별 별도 조회가 서로 배타적이라고 가정하지 않는다.
6. source window·scope·cap·warning·권한 경고·dedup 정책·수집 시각을 집계와 함께 저장한다.
7. API는 `returned_records`와 제품이 계산한 `deduplicated_records`를 구분한다. `complete_for_declared_query`도 시간 경계·권한·노드 scope가 검증된 범위에서만 true다. `complete_for_entire_server=true`는 현재 근거로 만들 수 없다.

메시지 provider의 **정상 0개**를 지표 provider의 **required44가 0개인 인증 의심**과 동일하게 다루지 않는다. 정상 메시지 0건마다 NWA 로그인을 반복하면 세션·부하 문제가 생긴다.

## MON 5 ChannelAdminServlet 상태 수집

### MON 5.1 READ_ONLY 전체·필터·단건 요청

전체 상태 조회:

```http
GET /AdapterFramework/ChannelAdminServlet?action=status&party=*&service=*&channel=*&status=all&shortLogCollect=false&showProcessLog=false&showAdminHistory=false
```

단건 상태 조회:

```http
GET /AdapterFramework/ChannelAdminServlet?action=status&channelID=00000000000000000000000000000001&status=all&shortLogCollect=false&showProcessLog=false&showAdminHistory=false
```

단건 예시의 32hex는 실제 객체를 뜻하지 않는 가짜값이다. 실제 호출은 backend가 이미 읽어 확인한 ID만 사용한다. `status=error`, `status=stopped`, `status=inactive`도 과거에 전체 목록의 해당 부분집합과 대조됐다. **`status=stopped`는 조회 필터이며 `action=stop`이 아니다.**

`GET /AdapterFramework/channelAdmin/ChannelAdmin.xsd`로 설치 XML 계약을 읽었다. Basic은 별도 client가 메모리에서 생성한다. 최초 실증은 Cookie 없이 성공했으며 이후 자체 jar를 사용했다. 외부 상태 조회를 위해 채널 제어 모드를 변경할 필요는 없다는 SAP 공식 설명이 있으나 본사 권한은 현재 계정으로 확인한다. 조회 action의 문헌상 이름은 `xi_af_channel_admin_display`다. 자동 권한 부여나 modify 권한 추가는 이 구현의 일부가 아니다.

### MON 5.2 고정 request builder

```python
# OFFLINE: 상대 요청 경로만 만든다. 실제 HTTP는 별도 READ_ONLY transport 사용.
import re
from urllib.parse import urlencode

GUID32 = re.compile(r"^[0-9A-Fa-f]{32}$")
STATUS_FILTERS = {"all", "ok", "error", "stopped", "inactive", "unknown", "unregistered"}

def channel_status_path(channel_id: str | None = None,
                        status_filter: str = "all") -> str:
    if status_filter not in STATUS_FILTERS:
        raise ValueError("unsupported_status_filter")
    pairs = [("action", "status")]
    if channel_id is None:
        pairs.extend([("party", "*"), ("service", "*"), ("channel", "*")])
    else:
        if not GUID32.fullmatch(channel_id):
            raise ValueError("channel_id_must_be_32hex")
        pairs.append(("channelID", channel_id))
    pairs.extend([
        ("status", status_filter), ("shortLogCollect", "false"),
        ("showProcessLog", "false"), ("showAdminHistory", "false"),
    ])
    return "/AdapterFramework/ChannelAdminServlet?" + urlencode(pairs)
```

`urlencode`가 `*`를 `%2A`로 표현하는 것은 URL encoding이며 의미는 동일하다. raw URL 문자열에 사용자 입력을 덧붙이지 않는다. 호출 직전에 method=GET·고정 path·action=status·로그/history false를 다시 검사한다. generic `action` 인자를 frontend DTO에 추가하지 않는다.

### MON 5.3 XML와 상태 모델

정상 XML은 namespace 없는 `ChannelStatusResult/Channels/Channel`이다. 치명 오류는 별도 root `ErrorInformation`으로 올 수 있으므로 목록 0개로 변환하지 않는다. start/stop 응답 root인 `ChannelAdminResult`도 이 읽기 provider에서는 계약 오류다.

| 필드 | 설치 계약 | 제품 모델 |
|---|---|---|
| `Party`, `Service`, `ChannelName` | string, 필수 | 표시·보조 식별. 이름 tuple만 전역 primary key로 쓰지 않음 |
| `ChannelID` | `[0-9A-Fa-f]{32}` | SID+AE scope+원형 ID. canonical 비교값과 원문 보존 |
| `AdapterType` | string | 필터/분류. 동명 어댑터 버전까지 추측하지 않음 |
| `Direction` | `INBOUND`, `OUTBOUND` | INBOUND=Sender, OUTBOUND=Receiver |
| `ActivationState` | `STARTED`, `STOPPED` | `activation_state` |
| `ChannelState` | optional: `OK`, `ERROR`, `INACTIVE`, `UNKNOWN`, `UNREGISTERED` | nullable `channel_state`; 요소 부재와 문자열 UNKNOWN 구분 |
| `Control` | `MANUAL`, `SCHEDULER`, `WEBSERVICE` | `control`; health와 별도 |
| `ShortLog`, `ProcessLog`, `AdminHistory` | optional | 이번 요청에서는 제외. 수집된 것처럼 표시하지 않음 |
| `AdminErrorInformation` | optional | 원문은 민감정보가 있을 수 있어 분류·마스킹 후 제한적으로 사용 |

과거 1,300개 응답에서 STOPPED/ChannelState 부재 1,087개, STARTED/OK 203개, STARTED/INACTIVE 8개, STARTED/ERROR 2개였다. 따라서 STARTED 213개를 정상 213개로 표시하면 안 된다. 해당 수치는 역사 스냅샷이며 본사 현재 개수나 기대값으로 테스트에 hardcode하지 않는다.

### MON 5.4 OFFLINE 상태 parser 예시

아래 예시는 MON 2.4의 `parse_bounded_utf8_xml` 함수를 같은 모듈에 둔 경우다. 예시에서 반환하는 모델은 SAP 원문과 제품 필드를 구분한다.

```python
# OFFLINE: bytes -> typed snapshot. HTTP·제어·저장 없음.
import re

def parse_channel_status(data: bytes) -> list[dict]:
    root = parse_bounded_utf8_xml(data, max_bytes=2_000_000)
    if root.tag == "ErrorInformation":
        raise ValueError("channel_service_error")
    if root.tag != "ChannelStatusResult":
        raise ValueError("unexpected_channel_response_root")
    channels = root.find("Channels")
    if channels is None:
        raise ValueError("channels_wrapper_missing")
    rows, seen = [], set()
    required = (
        "Party", "Service", "ChannelName", "ChannelID", "AdapterType",
        "Direction", "ActivationState", "Control",
    )
    for node in channels.findall("Channel"):
        if any(len(node.findall(name)) != 1 for name in required):
            raise ValueError("missing_or_duplicate_channel_field")
        if len(node.findall("ChannelState")) > 1:
            raise ValueError("duplicate_channel_state")
        raw = {name: node.findtext(name, default="") for name in required}
        channel_id = raw["ChannelID"]
        if not re.fullmatch(r"[0-9A-Fa-f]{32}", channel_id):
            raise ValueError("invalid_channel_id")
        canonical_id = channel_id.lower()
        if canonical_id in seen:
            raise ValueError("duplicate_channel_id_in_scope")
        seen.add(canonical_id)
        state_node = node.find("ChannelState")
        state = None if state_node is None else (state_node.text or "")
        known = (
            raw["Direction"] in {"INBOUND", "OUTBOUND"}
            and raw["ActivationState"] in {"STARTED", "STOPPED"}
            and raw["Control"] in {"MANUAL", "SCHEDULER", "WEBSERVICE"}
            and state in {None, "OK", "ERROR", "INACTIVE", "UNKNOWN", "UNREGISTERED"}
        )
        rows.append({
            "raw": raw, "channel_id": canonical_id,
            "activation_state": raw["ActivationState"],
            "channel_state": state, "control": raw["Control"],
            "contract_status": "KNOWN" if known else "UNKNOWN_CODE",
        })
    # 저장된 XSD의 Channel minOccurs 기본값은 1이다. 빈 목록도 임의 정상 처리하지 않는다.
    if not rows:
        raise ValueError("empty_channel_list_requires_installation_validation")
    return rows
```

공유된 익명화 response의 ID는 `anon_...` 형식이라 원본 GUIDType을 만족하지 않는다. 테스트에서는 익명 ID를 **가짜 32hex ID로 명시적으로 변환한 synthetic fixture**를 사용하거나 익명화 자료의 구조 QA와 원본 XSD QA를 분리한다. 익명화 XML을 raw response라고 주장하지 않는다.

### MON 5.5 기존 Systatus와 연결할 때

기존 화면을 없애고 servlet 하나로 모든 필드를 대체하지 않는다. `Systatus.getChannInfo`와 이 endpoint는 field·scope가 다르다. 과거 두 경로 모두 1,300행이었지만 동일 시점 전수 ID 대조는 수행하지 않았다. 과거 Systatus warning 8개와 servlet INACTIVE 8개의 개수가 같다고 state mapping을 확정할 수 없다.

1. 같은 계정·AE·동일한 짧은 시간창에서 두 읽기 결과를 얻는다.
2. ID 원형과 canonical ID를 모두 보존하고 실제 대응을 검사한다. 이름은 보조 대조다.
3. 매칭·미매칭·중복·scope 차이를 별도로 기록한다.
4. API에 `activation_state`, `channel_state`, `control`, `raw_status`, `state_source`를 추가한다. 기존 `status`는 호환용 파생값이더라도 Unknown/미제공을 Running으로 치환하지 않는다.
5. 전체성 미확정 snapshot에서 사라진 ID를 즉시 삭제·장애 복구로 판정하지 않는다.

### MON 5.6 상태 이력과 알림 제안

서버·AE scope·ChannelID별 snapshot을 저장하고 이전 성공 snapshot과 비교해 이벤트를 만든다. `OK→ERROR`, `ERROR→OK`, activation 변경과 control 변경을 다른 사건 종류로 둔다. 주기 수집으로 얻는 `first_observed_at`은 실제 장애 발생 시각과 다를 수 있으므로 `actual_started_at`으로 이름 붙이지 않는다.

중요 채널·예상 운용 시간·최소 지속 조건·maintenance window·중복 억제·복구 통보를 제품 정책으로 등록한다. STOPPED나 INACTIVE를 무조건 장애로 처리하지 않는다. 재시작 후 열린 사건을 복구하고 확인 상태를 durable하게 저장한다. 이 알림 엔진은 설계 제안이며 REA에서 완성된 알림 API를 발견한 결과가 아니다.

## MON 6 공통 전송과 수집 결과 계약

### MON 6.1 transport는 인증·호출 정책만 공유한다

기존 client의 서버 registry·timeout·명시적 host alias를 재사용하되 다음 세 transport profile을 분리한다.

- `as_java_metrics_session`: NWA form session jar와 required44 parser.
- `adapter_message_basic`: 표준 메시지 Basic binding과 bounded filter/parser.
- `channel_status_basic`: servlet status 전용 GET builder/parser.

GET/HEAD/OPTIONS만 retry하는 현재 일반 HTTP retry 설정을 POST 전체로 넓히지 않는다. SOAP 읽기 재시도는 operation allowlist·같은 고정 요청 identity·한도·backoff를 갖춘 provider 레벨에서 구현한다. 작성 자동화의 create/change/activate는 이 read retry 정책을 공유하지 않는다.

HTML, SOAP Fault, `ErrorInformation`, schema mismatch, partial data를 별도 오류로 만든다. Exception 본문 전체나 requests prepared request를 로그에 dump하지 않는다. 외부 응답에 SAP 내부 exception·원문 URL·계정·XML을 그대로 반환하지 않는다.

### MON 6.2 READ_ONLY 전송을 연결하는 예시

다음 예시는 호출을 실행하면 실제 읽기 HTTP가 발생하는 adapter 골격이다. 자동 실행용 스크립트가 아니며 세션·origin·한도는 기존 backend 설정에서 주입한다. NWA form 로그인은 별도 인증 adapter가 완료한 뒤 지표 session을 전달한다. `requests.Session`을 사용한다면 지표 session은 Basic auth를 자동 첨부하는 기존 `build_session`과 구분해 `session.auth is None`으로 유지한다. 메시지·채널 session에는 기존 secret provider가 Basic 인증을 설정할 수 있다.

```python
# READ_ONLY: 이 함수를 호출할 때만 실제 HTTP 읽기가 발생한다.
# session/origin은 backend가 승인한 서버 profile에서만 제공한다.
from urllib.parse import urlsplit

def fetch_monitoring_xml(session, origin: str, operation: str,
                         request_bytes: bytes | None,
                         connect_timeout_s: float, read_timeout_s: float,
                         max_bytes: int, channel_id: str | None = None) -> dict:
    parsed = urlsplit(origin)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
        raise ValueError("invalid_configured_origin")
    if min(connect_timeout_s, read_timeout_s, max_bytes) <= 0:
        raise ValueError("positive_transport_limits_required")
    headers = {"Accept": "application/xml, text/xml"}
    if operation == "metrics44":
        if session.auth is not None:
            raise ValueError("metrics_profile_requires_own_session_cookie_auth")
        path = "/_tc~monitoring~webservice~web/JEEMONWSService"
        method = "POST"
        headers["Content-Type"] = 'text/xml; charset="UTF-8"'
        # 과거 독립 collector와 같이 SOAPAction을 임의 합성하지 않는다.
    elif operation == "message_list":
        path = "/AdapterMessageMonitoring/basic?style=document"
        method = "POST"
        headers.update({"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": '""'})
    elif operation == "channel_status":
        path = channel_status_path(channel_id=channel_id)
        method = "GET"
        if request_bytes is not None:
            raise ValueError("channel_status_get_has_no_body")
    else:
        raise ValueError("operation_not_in_read_allowlist")
    if method == "POST":
        if not request_bytes:
            raise ValueError("soap_request_body_required")
        request_root = parse_bounded_utf8_xml(request_bytes, max_bytes=2_000_000)
        request_body = request_root.find(f"{{{SOAP11}}}Body")
        expected_qname = (
            f"{{{METRICS_NS}}}retrieveMonitors" if operation == "metrics44"
            else f"{{{MSG_NS}}}getMessageList"
        )
        if (request_root.tag != f"{{{SOAP11}}}Envelope" or request_body is None
                or len(request_body) != 1 or request_body[0].tag != expected_qname):
            raise ValueError("soap_body_not_in_read_allowlist")
    with session.request(
        method, origin.rstrip("/") + path, data=request_bytes,
        headers=headers, timeout=(connect_timeout_s, read_timeout_s),
        allow_redirects=False, stream=True,
    ) as response:
        chunks, size = [], 0
        for chunk in response.iter_content(chunk_size=65_536):
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("response_size_limit")
            chunks.append(chunk)
        return {
            "http_status": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "body": b"".join(chunks),
        }
```

호출자는 HTTP/HTML/Fault/정상 wrapper를 provider별로 해석하고 원문 `body`를 그대로 API·로그·LLM으로 전달하지 않는다. 메모리에서 parser를 거친 최소 DTO만 저장한다. SOAP/servlet 요청의 3xx는 이 예시에서 자동 추적하지 않으므로 인증 redirect로 분류하고 승인된 로그인 흐름만 별도로 수행한다. 로그인 form GET/POST의 redirect 허용 정책과 데이터 읽기 요청의 redirect 정책은 서로 다르다.

### MON 6.3 제안하는 common envelope

다음은 **자체 제품 API의 제안**이며 SAP의 응답 형식이 아니다.

```json
{
  "data": [],
  "meta": {
    "sid": "POX",
    "source_service": "channel_admin_status",
    "contract_version": "installation-contract-sha256",
    "collected_at": "2026-01-01T00:00:00Z",
    "last_success_at": "2026-01-01T00:00:00Z",
    "collection_status": "COLLECTED",
    "stale": false,
    "completeness": "UNKNOWN_GLOBAL_SCOPE",
    "query_window": null,
    "caller_scope": "configured-sid-and-ae",
    "limitations": ["node-level coverage not established"],
    "error_category": null
  }
}
```

`caller_scope`에 사용자명이나 계정 식별자를 공개하지 않는다. 내부에서 권한 scope ID와 관계를 보존하면 충분하다. `collected_at`은 수집기의 관측 시각이고 source timestamp가 아니다. 메시지 `date`나 개별 timestamp를 별도 필드로 두고 수집 지연을 혼동하지 않는다.

| 상황 | data 처리 | meta/UI 처리 |
|---|---|---|
| 최신 정상 수집 | 새 snapshot | 성공 시각·scope 표시 |
| 일시 실패 | 마지막 정상값 보존 가능 | 현재 실패·stale 표시. 최신값처럼 표시 금지 |
| 정상 메시지 0건 | 빈 목록 | 실제 조회 구간·인증/계약 성공·경고 상태 표시 |
| 지표 required44의 0건 | 0으로 채우지 않음 | AUTH_SUSPECT/복구 결과 |
| 상한 도달/권한 경고 | 반환된 부분 목록 보존 | PARTIAL·누락 이유. 전체 건수 라벨 금지 |
| 미확정 단위·상태 | 원시값 보존 | Unknown/단위 미확정. 초록 정상 기본값 금지 |
| source 미설정 | 운영 샘플로 대체하지 않음 | NOT_CONFIGURED 또는 명시적 DEMO 출처 |

### MON 6.4 스케줄링과 부하

기존 Collector scheduler를 재사용하고 화면마다 별도 polling 수집기를 추가하지 않는다. 한 서버의 동일 source는 공유 snapshot을 제공한다. 주기·concurrency·request budget은 설치의 허용 부하에서 측정해 설정한다. 본 문서의 실증 간격 10초·16초·75초 등을 운영 권장 polling 주기로 복사하지 않는다.

수집 실패를 새 로그인 폭주·전체 WSDL 재다운로드·모든 AE 재조회로 확대하지 않는다. WSDL/client cache는 contract version·credential generation·session ownership 변경 시 invalidation한다. 여러 backend instance를 운영하면 프로세스 내부 Lock만으로 중복 scheduler를 막을 수 없으므로 existing durable lease를 확장한다.

## MON 7 에이전트용 구현 순서와 수용 기준

### MON 7.1 먼저 만들 수 있는 오프라인 작업

1. 이 장의 relative endpoint·QName·44개 정의를 versioned config로 옮긴다.
2. transport를 사용하지 않는 요청 builder와 response parser를 구현한다.
3. 민감값 없는 synthetic fixture를 만든다. 실제 호스트·업무 ID를 복사하지 않는다.
4. 기존 API의 source/DEMO 분기·상태 변환을 새로운 envelope와 호환시키는 adapter를 추가한다.
5. 스키마 변경은 새 migration으로만 추가하고 snapshots/events/auth cooldown의 저장 경계를 분리한다.
6. 신규 read provider는 default off로 등록하고 서버별 capability와 frontend 상태를 연결한다. 설정되지 않았으면 NOT_CONFIGURED로 표시한다.

### MON 7.2 의미 있는 오프라인 시험 목록

| ID | 시험 | 통과 기준 |
|---|---|---|
| MON-T01 | 44정의 builder | 고유 요청 label44·monitorName37·필드 순서·QName·path 원형 일치 |
| MON-T02 | 평균 CPU path | `CPUCPU_Utilization`을 자동 교정하지 않음 |
| MON-T03 | 지표 정상/alias | StartedNodes/FailedNodes만 canonical label로 대응, 정확히44개 수락 |
| MON-T04 | 지표 실패 fixture | 0/43/45개·중복·monitorName/agg 불일치·NaN/Infinity·SOAP Fault·HTML 거부 |
| MON-T05 | 세션 singleflight | 동시 인증 상실에 로그인 1개만 수행, account/server 사이 jar 분리 |
| MON-T06 | 로그인 form | hidden 유지·actual action 사용·외부 origin 차단·form없음/복수/비밀번호오류 분리 |
| MON-T07 | 복구 한도 | 한 collect에서 재로그인·재수집 각각 제한, 재시작 간 cooldown 유지 |
| MON-T08 | 메시지 builder | MSG/FILTER namespace 구분·sequence·timezone·양수cap·고정window 유지 |
| MON-T09 | 메시지 parsing | 단건/다건/0건·nil·warning·권한 경고·boolean false를 정확히 구분 |
| MON-T10 | 메시지 집계 | cap도달·동일timestamp밀집·경계중복·status중복·maxrequests 종료를 PARTIAL로 표시 |
| MON-T11 | 채널 request | 어떤 입력에도 action=status, 로그/history false,32hex검증 유지 |
| MON-T12 | 채널 상태 | STARTED+ERROR, STARTED+INACTIVE, STOPPED+ChannelState없음, UNKNOWN을 각각 보존 |
| MON-T13 | 채널 응답 오류 | ErrorInformation/ChannelAdminResult/중복ID/잘못된GUID/새enum을 정상 Running으로 처리하지 않음 |
| MON-T14 | snapshot 사건 | 장애 첫관측·재발·확인·복구를 보존, partial scope 누락으로 삭제하지 않음 |
| MON-T15 | secret canary | 가짜 credentials/header/token/XML 민감필드를 주입해 로그·API·DB감사출력·LLM문맥에 평문이 없는지 확인 |
| MON-T16 | no-write | transport spy에서 채널제어·메시지조작·payload·cache refresh·job 실행 요청이 0개 |
| MON-T17 | UI 정확도 | source미설정/실패/부분/오래된값/정상0건을 서로 다른 상태로 표시 |

### MON 7.3 본사 읽기 실증 완료 조건

- 설치 원본 WSDL/XSD와 profile hash를 기록하고 source version을 고정한다.
- 실제 계정 권한에서 작은 고정 시간창의 메시지 read, 전체/단건 채널 status를 비교한다. 인증 대조는 계정 잠금·부하 한도 안에서 정해진 소수 요청만 사용한다.
- 지표는 독립 jar 최초 로그인→44개→동일 jar 재수집을 확인한다. 자연 만료와 SSO 복원은 별도 시험 결과로 남긴다.
- 본사 NWA와 동일 시점·동일 필터의 표시를 대조하고 단위·변환·scope 차이를 기록한다. 다른 시각의 값 차이를 parser 오류로 단정하지 않는다.
- 운영 부하·동시 세션 수·relogin rate·stale 복구·장시간 수집을 측정한다. 테스트를 실행하지 않았으면 status는 NOT_RUN이다.
- 모든 결과는 검증한 SID·AE·계정 가시성·시간 범위를 포함한다. 성공 응답을 ‘전체 PO 정상’으로 확장하지 않는다.

## MON 8 원본 근거 위치와 무결성 확인

`RESEARCH_ROOT`는 별도 전달한 조사 자료 루트다. GitHub Markdown만으로 원본 HAR·JAR·서버 Cookie·원본 WSDL이 자동 제공되는 것은 아니다. 아래 경로는 상대 경로이며 민감값 검토 없이 원본 폴더 전체를 Git에 추가하지 않는다.

| 경로 (`RESEARCH_ROOT` 기준) | 용도 | SHA-256 |
|---|---|---|
| `pimon-analysis-20261015/soap-session-44-verification/request.xml` | 정상44개 요청 정의 | `aa001ec43c79a0682ec5547812c134b18a00cabee6d812c9da23a8e2b96755ff` |
| `pimon-analysis-20261015/nwa-readonly/metrics-contract.csv` | 44개 전체 대응표 | `ad0ab6d14908689fb69c39e1ce4e9e252916f4b108c357ae5f414360b04b8803` |
| `pimon-analysis-20261015/collector-session-verification/verification.json` | 독립로그인·Cookie상실복구·자연만료미검증 | `a1c456d0009e06691cd17ddf6ef3ce0273126102255d8d6f5bac9ba006033cf7` |
| `pimon-analysis-20261018/standard-message-soap/qa-contract.json` | 메시지 QName·sequence·상한 해석 | `46dc153244ecde7165d2f18b71bc56e72ba4b62441ede9c5131ac7002a5a2122` |
| `pimon-analysis-20261018/standard-message-soap/06-past-window-max100.request.xml` | 실제 성공한 최소 필터·순서 | `6a95d45a5a8114ce8688a51acff3ced5cae6e6e437b6b0a898ef41a5c5baa0a4` |
| `pimon-analysis-20261018/standard-channel-status/ChannelAdmin.xsd` | 채널 XML type/enum/optional 계약 | `aef91f5ebd748c7c5c3f6ce24fda0a1a29f6f63476201bb735c714f3591813fa` |

추가 근거는 각 폴더의 `findings.md`, `verification.json`, `qa.json`, `rea-evidence.json` 또는 `rea-final-evidence.json`에 있다. HTTP raw 원본 bytes의 hash와 익명화·재직렬화 공유본 hash는 다르다. HAR의 wait에 client 전체 경과시간을 배치한 자료는 네트워크 단계별 latency 분석으로 사용하지 않는다.

# AUT 개발 자동화 프로토타입과 실행기 구현 지침

작성 기준은 2026-10-19까지의 보존 연구다. 현재 제품 구현이나 실제 SAP 생성 성공을 의미하지 않는다.
## AUT 1 목적과 검증 경계

본 장은 기존 SAP PO에 연결하는 외부 객체 작성기 지침이다. Python이 입력·계획·검증·실행 기록을 담당하고, Directory는 SOAP adapter, ESR은 버전을 고정한 별도 Java worker로 접근한다. SAP DB 직접 쓰기나 신규 메시지 어댑터 배포는 선행 조건이 아니다.

기본 모드는 OFFLINE_PLAN_ONLY다. 본 문서를 전달받았다는 사실은 SAP create/change/edit/openForEdit/save/compile/activate/submit, CL 생성, 채널 제어, 시험 메시지 전송을 허가받았다는 뜻이 아니다. 실제 실행은 별도 테스트 환경·대상·허용 동작을 정한 후속 단계다. 실제 host·계정·secret은 사내 config/secret 경로에서만 공급한다.

| 증거 | 확인한 내용 | 확인하지 않은 내용 |
|---|---|---|
| SDK 45 JAR | JNLP 선언 순서·크기·SHA·ZIP CRC·클래스 인벤토리 | 최소 JAR 집합·암호학적 서명 검증·SAP 지원/라이선스 |
| BootstrapProbe | 로컬 property·session delegate·bean metadata 7단계 통과 | 원격 login·JNDI lookup·쓰기 권한 |
| Model/MappingProbe | 7+6=13개 로컬 시나리오 통과 | 서버 wire 수락·영속 저장·compile·activate·편집기 재열기 |
| Directory 계약 | WSDL 4종, Body 예제 10개 XSD 통과, 부정 사례 6개 거부 | Envelope/HTTP·권한·SAP 업무 일관성·실제 생성 |
| 구현 준비 | BS27+MD52+OR62=141개 요구·근거·다음 시험 | 진행률·141개 서버 시험 통과·제품 완성 |

근거는 RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness 아래 implementation-spec.md, verification-summary.json, bootstrap-findings.md, models-findings.md, orchestration-findings.md, readiness-ledger.json이다. Java public 메서드라는 사실을 SAP 공식 지원 SDK라고 해석하지 않는다. 원본 JAR·JNLP·WSDL·probe를 이 공개 Markdown에 첨부한 것은 아니며 사내에서 권한 있게 확보해야 한다.

## AUT 2 첫 프로토타입의 지원 범위

- 단일 SWCV/namespace, source/target DT·MT 각 하나.
- STATELESS·document-oriented SI 각 하나, OUTBOUND/INBOUND·NORMAL·비동기 operation 하나.
- UDF/lookup 없는 direct MM 하나, operation과 MM을 연결하는 OM 1:1.
- Channel 두 개·ICO 하나의 논리 계획. 어댑터 속성은 별도 검증된 template에서 해결.
- 명세 입력→typed DTO→참조 DAG→사전 검증→계획·diff→내보내기/재읽기.
- SDK가 사내에 있을 때만 guarded local serialize/load 시험을 추가.
- 모든 결과에 evidence_scope와 live_verified=false를 보존. mutation dispatch는 0.

sync response/fault, multi-operation·receiver, 조건/dynamic receiver, EOIO, UDF, 외부 archive/library, DB/RFC lookup, 기존 객체 clone/update는 별도 capability다. API enum 존재만으로 지원을 선언하지 않는다.

## AUT 3 완전한 최소 논리 명세

자체 제품 입력 제안이며 SAP payload나 기존 API가 아니다. 모든 이름·secretRef는 가짜다. 아래는 ESR 8객체+Directory 3계획의 논리 명세로 완전하지만, symbolic SWCV와 미해결 어댑터 template/secret 때문에 원격 실행은 불가하다.

~~~json
{
  "schemaVersion": "1",
  "mode": "OFFLINE_PLAN_ONLY",
  "sid": "POX",
  "namespace": "urn:example:order",
  "masterLanguage": "EN",
  "context": {
    "kind": "symbolic",
    "softwareComponentVersion": "EXAMPLE_SWCV",
    "resolvedGuid": null
  },
  "capabilities": {
    "asyncOneToOne": true,
    "directFieldMapping": true,
    "udf": false,
    "lookup": false,
    "updateExisting": false,
    "clone": false
  },
  "objects": [
    {
      "id": "dt_source", "kind": "DT", "action": "create",
      "name": "DT_Order_Source",
      "fields": [
        {"name": "order_no", "type": "xsd:string", "minOccurs": 1, "maxOccurs": 1},
        {"name": "amount", "type": "xsd:decimal", "minOccurs": 1, "maxOccurs": 1}
      ]
    },
    {
      "id": "dt_target", "kind": "DT", "action": "create",
      "name": "DT_Order_Target",
      "fields": [
        {"name": "OrderId", "type": "xsd:string", "minOccurs": 1, "maxOccurs": 1},
        {"name": "Amount", "type": "xsd:decimal", "minOccurs": 1, "maxOccurs": 1}
      ]
    },
    {
      "id": "mt_source", "kind": "MT", "action": "create",
      "name": "MT_Order_Source", "dataTypeRef": "dt_source",
      "payloadNamespace": "urn:example:order:source", "rootName": "MT_Order_Source"
    },
    {
      "id": "mt_target", "kind": "MT", "action": "create",
      "name": "MT_Order_Target", "dataTypeRef": "dt_target",
      "payloadNamespace": "urn:example:order:target", "rootName": "MT_Order_Target"
    },
    {
      "id": "si_source", "kind": "SI", "action": "create",
      "name": "SI_Order_Out", "category": "OUTBOUND",
      "pattern": "STATELESS", "documentOriented": true,
      "operations": [
        {
          "id": "op_source", "name": "processOrder", "pattern": "NORMAL",
          "mode": "ASYNCHRONOUS", "requestMessageRef": "mt_source",
          "responseMessageRef": null, "faultMessageRefs": []
        }
      ]
    },
    {
      "id": "si_target", "kind": "SI", "action": "create",
      "name": "SI_Order_In", "category": "INBOUND",
      "pattern": "STATELESS", "documentOriented": true,
      "operations": [
        {
          "id": "op_target", "name": "processOrder", "pattern": "NORMAL",
          "mode": "ASYNCHRONOUS", "requestMessageRef": "mt_target",
          "responseMessageRef": null, "faultMessageRefs": []
        }
      ]
    },
    {
      "id": "mm_order", "kind": "MM", "action": "create", "name": "MM_Order",
      "sourceMessageRef": "mt_source", "targetMessageRef": "mt_target",
      "rules": [
        {
          "kind": "direct",
          "source": {"namespace": "urn:example:order:source", "path": ["MT_Order_Source", "order_no"]},
          "target": {"namespace": "urn:example:order:target", "path": ["MT_Order_Target", "OrderId"]}
        },
        {
          "kind": "direct",
          "source": {"namespace": "urn:example:order:source", "path": ["MT_Order_Source", "amount"]},
          "target": {"namespace": "urn:example:order:target", "path": ["MT_Order_Target", "Amount"]}
        }
      ],
      "parameterDefinitions": [], "archives": [], "functionLibraries": []
    },
    {
      "id": "om_order", "kind": "OM", "action": "create", "name": "OM_Order",
      "sourceOperationRef": "op_source", "targetOperationRef": "op_target",
      "requestMappingRefs": ["mm_order"],
      "sourceMultiplicity": {"position": 0, "minOccurs": "1", "maxOccurs": "1"},
      "targetMultiplicity": {"position": 0, "minOccurs": "1", "maxOccurs": "1"}
    }
  ],
  "directory": {
    "channels": [
      {
        "id": "channel_sender", "action": "create", "party": "",
        "component": "BS_EXAMPLE_SOURCE", "name": "CC_Order_Sender",
        "direction": "Sender", "adapterTemplateRef": "example_sender_template",
        "secretRefs": []
      },
      {
        "id": "channel_receiver", "action": "create", "party": "",
        "component": "BS_EXAMPLE_TARGET", "name": "CC_Order_Receiver",
        "direction": "Receiver", "adapterTemplateRef": "example_receiver_template",
        "secretRefs": ["EXAMPLE_SECRET_REF_NOT_RESOLVED"]
      }
    ],
    "ico": {
      "id": "ico_order", "action": "create", "contract": "ICO750",
      "senderComponent": "BS_EXAMPLE_SOURCE", "senderParty": "",
      "senderInterfaceRef": "si_source", "senderOperationRef": "op_source",
      "senderChannelRef": "channel_sender",
      "receiverComponent": "BS_EXAMPLE_TARGET", "receiverParty": "",
      "receiverInterfaceRef": "si_target", "operationMappingRef": "om_order",
      "receiverChannelRef": "channel_receiver", "qualityOfService": "EO"
    }
  },
  "execution": {
    "dispatchEnabled": false, "activationEnabled": false, "runtimeTestEnabled": false
  }
}
~~~

ESR namespace와 MT payloadNamespace는 다를 수 있다. 자동 통합하지 않는다. path 배열은 자체 표현이며 SDK path token이 아니다. SDK 트리의 QName·부모 경로로 resolve한 결과를 사용한다.

## AUT 4 계획기·검증 알고리즘

다음은 SAP·Java 호출이 없는 자체 알고리즘 예제다. Directory validation, 이름·타입·크기 검사 등은 아래 수용 조건에 따라 추가한다.

~~~python
# OFFLINE: 실제 DTO와 예외 계층으로 구현할 개념 예제
from graphlib import TopologicalSorter, CycleError

def build_plan(manifest):
    if manifest["mode"] != "OFFLINE_PLAN_ONLY":
        raise ValueError("prototype supports OFFLINE_PLAN_ONLY")
    flags = manifest["execution"]
    if any(flags.get(k) for k in
           ("dispatchEnabled", "activationEnabled", "runtimeTestEnabled")):
        raise ValueError("remote effects disabled")
    nodes, dependencies, operation_owner = {}, {}, {}

    def add(key, value):
        if not key or key in nodes:
            raise ValueError("missing or duplicate logical id")
        nodes[key] = value
        dependencies[key] = set()

    for obj in manifest["objects"]:
        add(obj["id"], obj)
        if obj["action"] != "create":
            raise ValueError("prototype supports create plans only")
        if obj["kind"] == "SI":
            for op in obj["operations"]:
                add(op["id"], {**op, "kind": "OPERATION"})
                operation_owner[op["id"]] = obj["id"]
                dependencies[op["id"]].add(obj["id"])

    def edge(owner, ref, kinds):
        if ref not in nodes or nodes[ref]["kind"] not in kinds:
            raise ValueError("missing or wrong-kind dependency")
        dependencies[owner].add(ref)

    for obj in manifest["objects"]:
        key, kind = obj["id"], obj["kind"]
        if kind == "MT":
            edge(key, obj["dataTypeRef"], {"DT"})
        elif kind == "SI":
            for op in obj["operations"]:
                edge(key, op["requestMessageRef"], {"MT"})
        elif kind == "MM":
            edge(key, obj["sourceMessageRef"], {"MT"})
            edge(key, obj["targetMessageRef"], {"MT"})
        elif kind == "OM":
            edge(key, obj["sourceOperationRef"], {"OPERATION"})
            edge(key, obj["targetOperationRef"], {"OPERATION"})
            for ref in obj["requestMappingRefs"]:
                edge(key, ref, {"MM"})
    try:
        order = list(TopologicalSorter(dependencies).static_order())
    except CycleError as exc:
        raise ValueError("reference cycle") from exc
    return {
        "mode": "OFFLINE_PLAN_ONLY",
        "esrStepIds": [key for key in order if nodes[key]["kind"] != "OPERATION"],
        "operationOwner": operation_owner,
        "remoteReady": False,
        "evidenceScope": "LOCAL_LOGICAL_PLAN",
        "liveVerified": False
    }
~~~

SI operation은 owner SI와 함께 저장하는 내부 객체이며 독립 create step으로 출력하지 않는다. Directory는 channel 2개→ICO 1개의 별도 DAG와 active ESR ref 조건을 추가한다.

생산 계획기의 필수 검사:

1. schemaVersion, JSON 크기/깊이/배열/문자열 상한, unknown field 정책.
2. ESR·operation·channel·ICO 전체 logical ID 중복·순환·참조 종류·누락.
3. XML NCName·namespace URI·type enum·min/maxOccurs lexical·범위·필드 중복. 대소문자/URI trailing slash 임의 통합 금지.
4. MT payload namespace·root·DT 구조, SI category/pattern/mode/request/response/fault 조합.
5. MM qualified path 유일성·type/반복 수·필수 target 누락·unsupported conversion 거부.
6. OM operation owner·category·mode·MT/MM signature·multiplicity 일치.
7. Channel party/component/direction/adapter template·ICO receiver/OM/target SI 일치.
8. local validation·remote resolution·server check를 별도 저장. local READY와 remote_ready 구분.
9. immutable plan revision과 normalizationVersion·SDK/WSDL fingerprint.
10. plan 함수의 SAP HTTP/JDBC/Java writer dispatch 0을 fake transport로 검사.

## AUT 5 SDK 환경 고정과 본사 재현

최종 검사 classpath는 Repository JNLP 선언 45 JAR 순서 그대로다. 25,453 클래스 출현·25,432 고유 entry·중복 21개 중 바이트가 다른 것은 AbstractAttribute.class 한 개였다. tenGenerics.jar가 maestro.core보다 먼저였다. alphabetic sort·임의 최신 Maven 라이브러리 혼합을 하지 않는다.

검증 runtime은 portable Temurin Java 8u504였다. Java 8 초과 major 53은 XJC JAR의 module-info.class 한 개였고 이를 전체 라이브러리 실행 불가로 확대하지 않는다. local probe 성공도 XJC 전 기능 호환성·Web Start package-part loading의 완전 재현을 보장하지 않는다.

| 파일 | 용도 |
|---|---|
| repository-acquisition.json | 45 JAR 순서·크기·SHA |
| classpath-inventory.json | 중복·major·서명 검증 한계 |
| runtime-acquisition.json | java/javac 경로·runtime pin |
| rea-inventory-summary.json | 새32+동일SHA 이전13의 REA 인벤토리 |
| probe-results/compiled-sources.json | source/class·classpath/runtime freshness |
| probes/GuardRunner.java·GuardSelfTest.java | Java API guard 설치·차단 검사 |
| probes/BootstrapProbe.java | 7단계 local bootstrap |
| probes/ModelProbe.java·MappingProbe.java | 7+6 model/mapping 시나리오 |

본사 이식 시 원본을 읽기 전용 보존하고 별도 작업 사본을 만든다. acquisition/runtime JSON에는 옛 머신 절대경로가 남아 있을 수 있다. 작업 사본에서 RESEARCH_ROOT와 local runtime으로 재바인딩하고 original→local path map·도구 버전·원본/사본 hash를 별도 기록한다. 원본 receipt를 새 경로로 덮어쓰지 않는다.

재현 순서: 사내 권한 있는 SDK 확보→SHA/크기/CRC·선언 순서 대조→지원 JDK와 binary hash 기록→작업 사본의 local path 재바인딩→guard/source 재컴파일→guarded probe 실행→semantic 결과·source pin 대조→새 결과/ledger 생성이다.

~~~powershell
# OFFLINE: 경로 재바인딩한 작업 사본의 implementation-readiness에서 실행
python run_offline.py compile GuardRunner GuardSelfTest BootstrapProbe ModelProbe MappingProbe
python run_offline.py run GuardSelfTest BootstrapProbe ModelProbe MappingProbe
python build_bootstrap_readiness.py
python models_analysis.py
python build_model_readiness.py
python build_orchestration_spec.py
python build_packet.py
python qa_readiness.py
~~~

원 runner는 javac -proc:none -source 8 -target 8, JVM -Xmx384m -Djava.awt.headless=true, probe 35초·compile 60초 상한을 사용한다. 이는 local 검사 상한이며 SAP 원격 timeout 검증값이 아니다. child 환경의 JAVA_TOOL_OPTIONS/_JAVA_OPTIONS/JDK_JAVA_OPTIONS/CLASSPATH를 제거하고 SDK/runtime/source/class hash 변경 시 재컴파일을 요구한다.

exit 0 외에 PROBE_JSON 한 레코드·completed=true·guard_installed=true·semantic_passed=true와 내부 실패 부재를 확인한다. SDK 일반 로그가 stdout에 섞이므로 전체 stdout을 JSON 한 개로 parse하지 않는다. 이전 실패 attempt를 보존한다.

SecurityManager guard는 Java API 차단 장치이며 OS sandbox/firewall·악성 코드·자격정보 격리 전체를 증명하지 않는다. optional jperflib native load와 localhost GUID 초기화 DNS 시도도 차단됐었다. 네트워크 시도가 전혀 없었다고 표현하지 않는다. offline worker에는 SAP credentials를 공급하지 않는다.
## AUT 6 ESR bootstrap·인증·세션

확인한 호출 가능 진입점은 해당 배포본의 계약이다. 다른 PO SP/patch에서도 같다고 가정하지 않는다.

| 순서 | 로컬 호출 | 의미 |
|---|---|---|
| 1 | com.sap.aii.utilxi.prop.api.AIIProperties.init(java.util.Properties) | 최초 property source |
| 2 | ApplicationComponent identity getter | Repository/Directory 역할 확인 |
| 3 | CoreSessionInformationProvider.getInstance().registerDelegate(ClientSessionInformationProvider.getInstance()) | local session delegate |
| 4 | LoginServiceProvider.getLoginService() | singleton 확보, 인증 아님 |
| 5 | LoginServiceProvider.registerBean(...) | bean metadata 등록, 원격 bean 획득 아님 |
| 6 | com.sap.aii.ib.bom.ifr.IfrTypeRegistration.register() | 공통 IFR factories/services |
| 7 | com.sap.aii.ibrep.bom.ifr.IfrTypeRegistration.register() | Repository IFR factories/services |
| 8 | MappingTypeRegistration.registerTypeServices/SerializationServices/LinkService | MM/OM factory·serializer·link registry |

짧은 class명과 registerBean의 정확한 import·overload·매개변수 순서는 BootstrapProbe.java와 bootstrap-evidence.json에서 확인한다. 생략 부호로부터 추측하지 않는다. 최소 bean 3개 등록이 모든 read path의 완전 registry는 아니다.

검증 identity는 REPOSITORY_WSCLIENT/REPOSITORY/J2EE_WSCLIENT였다. automatic role discovery는 classpath에 영향을 받으므로 Repository·Directory·server 라이브러리를 임의 혼합하지 않는다.

검증한 property는 com.sap.aii.connect.repository.contextroot와 com.sap.aii.ib.client.applicationname.repository다. 일반 Properties에는 com.sap.aii... 이름을 쓰며 JNLP adapter의 jnlp. prefix를 그대로 복사하지 않는다. host/port/전체 production profile은 미검증이다.

| Registry key | Home interface | 서버 구현 class 문자열 |
|---|---|---|
| LoginServiceBean | com.sap.aii.ib.sbeans.login.LoginServiceHome | com.sap.aii.ib.server.login.LoginServiceBean |
| ObjectAccessBean | com.sap.aii.ib.sbeans.oa.ObjectAccessHome | com.sap.aii.ib.server.oa.ObjectAccessBean |
| ChangeListMgmtBean | com.sap.aii.ib.sbeans.clmgmt.ChangeListMgmtHome | com.sap.aii.ib.server.clmgmt.ChangeListMgmtBean |

메타데이터 등록은 server class local load·원격 생성·인증이 아니다. SWCV/workspace/query/locator/schema 계산은 사용 path별 bean을 추가 확인한다. offline registry 점검에 getBusinessInterface나 login을 자동 포함하지 않는다.

AIIProperties.init 재호출은 INFO 후 기존 초기화를 유지할 수 있다. server reset API로 쓰지 않는다. LoginService singleton·client session·ServiceBase registry·remote factory/cache는 JVM 범위 공유 상태다. 기본 격리는 SID+계정+SDK fingerprint별 전용 JVM, worker 내부 SDK 호출 직렬화다. 동시 worker·세션 상한은 실측 후 정한다.

### AUT 6.1 6인자 login 계약

정적 선언과 분기에서 확인한 signature다. 이번 조사에서 호출한 원격 인증 코드가 아니다.

~~~text
login(String enteredUserName, String password, String newPassword,
      Language lang, DebugRouterData data, String logonTicket)
~~~

- enteredUserName은 호출 전에 trim·빈값 검증. 내부 trim 전에 sessionUsername으로 원본을 복사한다.
- 비밀번호 모드 password는 null 불가. handler가 toCharArray를 호출한다.
- 일반 로그인 newPassword=null. 빈 문자열도 password-change callback에 공급될 수 있다.
- lang은 실제 환경에서 허용한 언어를 사용. null·임의 default 미검증.
- 일반 연결 DebugRouterData=null. 임의 server/router override 금지.
- 비밀번호 모드 logonTicket=null. 빈 ticket으로 SSO 흉내를 내지 않는다.
- 원격 연결 전에 local session이 생성된다. hasSession=true는 인증 성공이 아니다.

자체 상태를 NEW→LOCAL_BOOTSTRAPPED→AUTHENTICATING→AUTHENTICATED로 분리한다. AUTHENTICATED는 실제 login 반환과 허용된 읽기 확인 후에만 설정한다. 현재 증거는 LOCAL_BOOTSTRAPPED까지다.

6인자 정상 경로에 GUI startup이 없다고 headless 원격 인증이 완성된 것은 아니다. 최초 login 실패·업무 RemoteException/일부 RuntimeException·reconnect는 BeanAccessHandler→ReconnectProcessor→Swing/EDT/대화상자→GUI login overload로 이어질 수 있다. headless=true나 worker restart만으로 이 최초 오류 경로를 해결하지 않는다.

LoginServiceProvider.registerBeanProxyProvider(BeanProxyProvider)는 public 업무 proxy hook이며 cache invalidate 후보지만 최초 login singleton의 오류 handler 교체 setter가 아니다. 이 hook 하나로 모든 GUI reconnect를 대체했다고 주장하지 않는다. 직접 EJB transport는 후속 후보이며 미구현·미인증이다.

logout은 remote logout/factory close를 하지만 local session/cache 완전 reset을 보장하지 않는다. ContextCleaner 10초 join도 cleanup 완료·업무 호출 timeout이 아니다. 확인하지 않은 JVM -D 옵션을 SAP timeout 설정으로 제시하지 않는다. 최초 정상/실패, 비밀번호 만료·계정 잠금·권한·연결 단절·세션 만료를 무인으로 분류하는 시험이 실제 작성 gate다.

## AUT 7 ESR 객체 키·참조·모델

| 식별자 | 의미 |
|---|---|
| logical ID | 계획 내부 별칭. SAP GUID 아님 |
| XiKey | type+name+ESR namespace, optional object GUID |
| VersionContext | SWCV/workspace 등 scope |
| VersionSpecifier | 특정 객체 version 선택 |
| server object/version GUID | 실제 조회·생성·저장 응답 |
| ChangeList context | repository별 저장/검사/활성화 경계 |
| operation reference | owner SI 내부 operation 반환 참조 |

확인한 local factory 표현은 다음이다. server create API가 아니다.

~~~text
XiKey.getNameInstance(XiTypeId, String name, String namespace) -> XiKey
TypeServiceProvider.getTypeService() -> TypeService
TypeService.newInstance(XiKey, VersionContext, Language) -> XiObject
VersionContext.Factory.getSwcInstance(GUID) -> VersionContext
XiObject.getObjectReference() -> XiReference
XiReference.getKey()/getContext()/getVersionSpecifier()
~~~

상속 메서드와 throws 등 exact 선언은 models-evidence.json 및 현재 설치 class를 대조한다. 이름만 맞는 다른 SWCV/context를 같은 대상으로 취급하지 않는다.

Registry에는 logical ID·kind·complete key·requested/resolved/server-returned ref·Active/User context·base/current version·CL/workspace·desired/readback digest·stage를 저장한다. SWCV/object/version/CL GUID를 하나의 uuid로 합치지 않는다. toString의 WKV/ID: 문자열을 identity API로 사용하지 않는다. local synthetic GUID를 실제 서버 ID처럼 제출하지 않는다.

실제 작성 설계는 symbolic dependency→remote resolve→fresh candidate→실제 저장 응답 ref 갱신→후속 객체 연결→readback 대조다.

### AUT 7.1 DT·MT

- DT는 com.sap.aii.ibrep.bom.ifr.DataType, 내용은 XsdSchema.
- target namespace·named complex/simple type·필드 순서·sequence/choice·min/maxOccurs·import/include·외부 reference 보존.
- primitive QName의 확인한 인자 순서는 XDOMFactory.getXName(localName,prefix,namespaceURI).
- DataType.setSchema/getSchema는 실제 상속 경로 포함 API를 사용.
- 다른 DT 참조는 XSD 문자열 외 TYPE link도 정합해야 함.
- MessageType.setDataType(XiReference), setXMLPayloadNS(String)로 DT ref와 payload namespace를 별도 지정.
- MT ESR namespace·payload namespace·root name·DT namespace를 합치지 않음.
- 일반 XSD-valid는 ESR schema check/activate 성공이 아님.
- null setter가 링크 제거 의미일 수 있으므로 생략/삭제·create/update DTO를 분리.

### AUT 7.2 SI와 내부 operation

local 통과 순서는 ServiceInterface→category→interface pattern→document orientation→createOperation→operation pattern→mode→message links다.

| 확인한 호출 | 용도 |
|---|---|
| ServiceInterface.setCategory(InterfaceCategory) | OUTBOUND/INBOUND |
| ServiceInterface.setInterfacePattern(InterfacePattern) | STATELESS 등 |
| ServiceInterface.setIsDocumentOriented(boolean) | document orientation |
| ServiceInterface.createOperation(String) -> Operation | owner SI 내부 operation 생성 |
| Operation.setOperationPattern(OperationPattern) | NORMAL 등 |
| Operation.setOperationMode(OperationMode) | sync/async |
| Operation.setRequestMessage(XiReference) | request MT |

operation key를 SI명+"."+이름으로 추측하지 않고 반환 operation ref를 쓴다. 실제 sync→async 전환에서 response link가 제거됐다. async에 response를 넣으면 InconsistentDefinitionException이 발생했다. fault setter도 기존 링크 제거 후 검사하는 경로가 있어 실패가 원본 model을 보존한다고 가정하지 않는다. 입력을 먼저 검증하고 fresh candidate에 적용한다. fault message와 일반 MT의 type 구분도 필요하다.

### AUT 7.3 MM graph·metadata·생성 Java

MM은 XiTransformation/XiTypeId.XI_TRANSFORMATION이다. SOURCE_IFR_MESS/TARGET_IFR_MESS, source/target schema, graph, metadata ZIP, Java source, parameter/structure properties, JDK, compiled JAR를 별도로 다룬다.

MappingTypeRegistration의 type/serialization/link registry 모두 필요하다. link registry 누락은 실제 초기 probe 실패 원인이었다. XIM import가 MT link를 ImportedMessage로 바꾸는 경로가 있어 실제 MT refs 보존을 검사한다.

graph는 Node·Src/Dest/Func brick·MappingGroup·Pin 연결을 보존한다. 확인한 단순 direct 연결은 다음이다.

~~~text
destination.getIns()[0].setLink(source.getOuts()[0])
~~~

Pin 연결과 생성 Java 보존이 반복 context·suppress·root 생성·업무 XML 결과 정합성을 보장하지 않는다. node.getPureName을 XML local name으로 오인하면 namespace 있는 XSD에서 실패한다. node.getXName().getName()·namespace URI·부모 경로를 사용하고 여러 후보가 걸리면 실패한다. SDK /ns0:Source/ns0:value token과 JSON path는 다른 표현이다. CommonConfigurator.makeMapping은 target 인자가 먼저라는 세부를 확인했다.

생성 class/package는 MM의 getProgramName/getPackageName에서 얻는다. 사용자 임의 Java class/package를 받지 않는다. JDK18 enum은 Java 1.8이며 Java 18 지시가 아니다.

Project.save/getMetaData는 없는 GUI MappingTool의 MTMemento에 접근해 NPE를 로그에 남기고 삼킬 수 있었다. ZIP 반환만으로 성공 판정 금지다. 최종 local probe는 public function storage→Transformation→test data→빈 customization→parameter serializer 경로로 기능을 저장하고 optional view memento를 제외했다. 새 Project load 후 생성 Java 동일성은 통과했지만 nonempty customization/template/library 보존, 서버·편집기 재열기는 미검증이다.

Project metadata ZIP timestamp는 고정되지 않는 경로가 있다. probe helper의 setTime(0)이 전체 SDK payload 결정성을 증명하지 않는다. raw SHA는 무결성, semantic canonical digest는 변경/중복 비교에 사용한다.

### AUT 7.4 UDF·parameter

FunctionDefinition.getSignature()는 public, setSignature(MethodSignatureDefinition)는 private다. reflection 우회 없이 공개 signature 객체를 구성하는 경로를 사용했다. MD-011은 V2V UDF 모델 XML roundtrip만 확인했고 FuncBrick 연결·Java compile/실행·서버 저장은 미검증이다. C2C/Q2Q·ResultList·init/cleanup/global/import·archive/library·OM/channel parameter는 별도 시험이다.

IDataAccess 구현은 상속한 IDbTableAccessor.getDbTabDefinitions도 필요했다. 직접 선언만 보고 stub을 만들지 않는다. 미지원 lookup을 가짜 성공값으로 반환하지 않는다.

### AUT 7.5 OM operation·message·program

OM은 Mapping/XiTypeId.MAPPING이다. source/target은 SI 자체가 아니라 내부 OPERATION refs다.

| 호출·role | 내용 |
|---|---|
| setLink(ILinkRole.Factory.getInstance("OUTBOUND_IF",0),sourceOpRef) | source operation |
| setLink(ILinkRole.Factory.getInstance("INBOUND_IF",0),targetOpRef) | target operation |
| setSourceIfSourceMessages(XiReference[]) | source request MT |
| setTargetIfTargetMessages(XiReference[]) | target request MT |
| setRequestProgramLinks(XiReference[]) | request MM 배열 |
| setSourceParameters/TargetParameters(SplitMergeAttributes.Parameter[]) | position·min/max |
| Multiplicity.determineMultiplicity(mapping) | multiplicity 계산 |
| getSourceIterfaces() | 해당 배포본의 실제 철자 |

1:1은 메시지 parameter 수/발생 수다. XML field unbounded와 혼동하지 않는다. category·mode·request/response/fault·program/property set·순서·multiplicity를 함께 검사한다. 편집기는 MappingAnalysis로 파생 links를 계산하지만 local fixture는 알려진 MT를 직접 넣었다. 원격 resolver 성공으로 확대하지 않는다.

## AUT 8 Directory wire 계약

기준은 RESEARCH_ROOT/pimon-analysis-20261018/jnlp-deep-analysis/wsdl의 설치 저장본이다. 본사에서 허용된 읽기로 원본 WSDL과 import를 다시 확보하고 fingerprint를 대조한다. 실제 origin은 사내 config로만 공급한다.

| 서비스 | WSDL 상대 경로 |
|---|---|
| Channel | /CommunicationChannelInService/CommunicationChannelInImplBean?wsdl |
| ICO legacy | /IntegratedConfigurationInService/IntegratedConfigurationInImplBean?wsdl |
| ICO750 | /IntegratedConfiguration750InService/IntegratedConfiguration750InImplBean?wsdl |
| ChangeList | /ChangeListInService/ChangeListInImplBean?wsdl |

POST binding endpoint는 WSDL soap:address를 따른다. ?wsdl을 무조건 POST 대상으로 쓰지 않는다. 내부 short host는 기존 명시 host_aliases만 configured origin으로 변환한다. 모든 외부 host를 rewrite하지 않는다. TLS·인증·권한·timeout·크기 제한은 본사 서비스별 검증 항목이다.

| 항목 | 저장 계약 |
|---|---|
| SOAP | 1.1 document/literal |
| Envelope URI | http://schemas.xmlsoap.org/soap/envelope/ |
| wrapper URI | http://sap.com/xi/BASIS |
| 공통 type URI | http://sap.com/xi/BASIS/Global |
| SOAPAction | http://sap.com/xi/WebService/soap1.1 |
| HTTP Content-Type | text/xml; charset=utf-8 |
| local child | unqualified |
| nil | nillable=false 필드의 xsi:nil 금지 |

SOAPAction은 SOAP1.1 client의 인용 문자열 header로 처리한다. prefix b는 바꿀 수 있지만 QName URI/local name·element 순서·child qualification은 유지한다. default xmlns=BASIS를 주면 local 자식까지 qualified돼 다르다.

Query/Read/확인된 상태조회만 read 목록에 넣는다. Create/Change/OpenForEdit/Delete/Revert/Activate/CL Create는 mutation이다. Check/CheckContent/compile의 부작용도 확인 전 read로 간주하지 않는다. Directory SOAP가 ESR 표준 create SOAP를 뜻하지 않는다.

### AUT 8.1 원본 fingerprint

| WSDL | SHA-256 |
|---|---|
| ChangeListIn-0.wsdl | ee7b3b051239cf00db7e4535d48f575bfe43b0f1e00a5a99c32d7c3e7cc513d1 |
| CommunicationChannelIn-0.wsdl | 7abb5e2104837dd6428d7cd9c32f6cc0ef354811359b2ef4c2e634e54882fb0d |
| IntegratedConfiguration750In-0.wsdl | 939a16e16a04e89ca61e006ed1a808536ad36f7719e616ffe2f303aeeac13d54 |
| IntegratedConfigurationIn-0.wsdl | 236a30303c5dccf3dd49f555e98901d533039d0b3ccc73731bdeb1f91e6d4f7e |

원본 WSDL에는 실제 endpoint가 포함되므로 공개하지 않는다. 사내 재수집본은 endpoint·재직렬화 차이와 schema 의미 차이를 분리해 검사한다. hash 변경을 무시하고 예전 DTO로 write하지 않는다.

## AUT 9 Channel typed DTO와 합성 예제

RestrictedCommunicationChannel의 필수값은 MasterLanguage, CommunicationChannelID, AdapterMetadata, Direction이다. Read와 Create/Change DTO를 분리한다.

| 항목 | 보존할 형태 |
|---|---|
| key | PartyID optional, ComponentID·ChannelID required. Party도 identity 일부 |
| AdapterMetadata | Name+Namespace+optional SWCV |
| Direction | Sender/Receiver |
| 단일 속성 | ordered (Name,Namespace?,Value?) 배열 |
| table 속성 | (Name,Namespace?,ValueTableRow[])→ValueTableCell(ColumnName,Value?) |
| module | ordered ProcessStep(ModuleName,ModuleType,ParameterGroupID) |
| parameter | 별도 group ID→Parameter[] 연결. group 존재 시 1개 이상 |
| administrative data | server owner/timestamp를 restricted 생성 DTO에 복사하지 않음 |
| 환경 의존 값 | credentialRef·인증서/키스토어·RFC destination/JDBC driver·adapter engine·polling 별도 resolve |

동명·다른 Namespace 속성을 dict[name]으로 합치지 않는다. 모듈 순서는 실행 의미가 있어 정렬 금지다. 반복 module과 table row/column을 평탄화하지 않는다. 일반 XSD 계약이 SFTP/JDBC/RFC 등의 업무 필수 속성을 모두 정하지는 않는다.

길이 상한은 party/component/channel 60, DesignObjectName 120, DesignObjectNamespace 255, SWCV/CL hyphen GUID 36, language 2, protocol 이름/version 10, description 255, CL name 80이었다. exact type/facet는 directory-contracts.json을 따른다. 기존 API의 channel 길이256을 작성 DTO에 재사용하지 않는다.

XSD는 객체0개 Create를 허용했다. 업무 validator는 최소1개+완전한 참조+필수 어댑터 값을 별도로 요구한다. Query의 ComponentID 생략 특례를 Create에 적용하지 않는다.

Channel create/activate 자체가 polling·외부 연결을 시작할 수 있다. Start/Stop 미호출만으로 runtime 영향 없음이라 표시하지 않는다. 이를 피하려고 자동 STOP/설정 변경을 끼워 넣지 않는다.

다음은 SCHEMA_ONLY 합성 예제다. 가짜 어댑터·모듈이며 업무 실행 설정이 아니다. 서버에 전송하지 않았다.

~~~xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Header/>
  <soapenv:Body>
    <b:CommunicationChannelCreateRequest xmlns:b="http://sap.com/xi/BASIS">
      <ChangeListID>11111111-1111-1111-1111-111111111111</ChangeListID>
      <CommunicationChannel>
        <MasterLanguage>EN</MasterLanguage>
        <CommunicationChannelID>
          <PartyID/><ComponentID>BS_EXAMPLE_SOURCE</ComponentID>
          <ChannelID>CC_EXAMPLE_SENDER</ChannelID>
        </CommunicationChannelID>
        <AdapterMetadata>
          <Name>EXAMPLE_ADAPTER</Name><Namespace>urn:example:adapter</Namespace>
          <SoftwareComponentVersionID>22222222-2222-2222-2222-222222222222</SoftwareComponentVersionID>
        </AdapterMetadata>
        <Direction>Sender</Direction><TransportProtocol>HTTP</TransportProtocol>
        <MessageProtocol>SOAP</MessageProtocol>
        <AdapterSpecificAttribute>
          <Name>example_nonsecret_property</Name>
          <Namespace>urn:example:adapter</Namespace><Value>example_value</Value>
        </AdapterSpecificAttribute>
        <AdapterSpecificTableAttribute>
          <Name>example_table</Name>
          <ValueTableRow><ValueTableCell>
            <ColumnName>example_column</ColumnName><Value>example_cell</Value>
          </ValueTableCell></ValueTableRow>
        </AdapterSpecificTableAttribute>
        <ModuleProcess>
          <ProcessStep>
            <ModuleName>example.module</ModuleName>
            <ModuleType>Local Enterprise Bean</ModuleType>
            <ParameterGroupID>example_group</ParameterGroupID>
          </ProcessStep>
          <ParameterGroup>
            <ParameterGroupID>example_group</ParameterGroupID>
            <Parameter><Name>example_parameter</Name><Value>example_value</Value></Parameter>
          </ParameterGroup>
        </ModuleProcess>
      </CommunicationChannel>
    </b:CommunicationChannelCreateRequest>
  </soapenv:Body>
</soapenv:Envelope>
~~~

SCHEMA_ONLY 합성 읽기 Body 예제는 다음이다. 실제 원격 읽기가 허용된 후 실제 key를 backend 메모리에서 채운다.

~~~xml
<b:CommunicationChannelReadRequest xmlns:b="http://sap.com/xi/BASIS">
  <ReadContext>Active</ReadContext>
  <CommunicationChannelID>
    <PartyID/><ComponentID>BS_EXAMPLE_SOURCE</ComponentID>
    <ChannelID>CC_EXAMPLE_SENDER</ChannelID>
  </CommunicationChannelID>
</b:CommunicationChannelReadRequest>
~~~

User context는 Active 검증과 다르며 current-user 변경을 포함할 수 있다. 정확한 가시성은 설치 계약·권한·현재 변경 상태로 확인한다. default 설명이 릴리스별로 다르므로 context를 명시한다. Party 없는 예제가 모든 key의 PartyID=""를 정당화하지 않는다.

## AUT 10 ICO750/legacy와 참조 투영

| 항목 | legacy | 750 |
|---|---|---|
| Create wrapper | IntegratedConfigurationCreateRequest | IntegratedConfiguration750CreateRequest |
| receiver type | Receivers | Receivers750 |
| ReceiverWildcardIndicator | 없음 | optional/default false |
| constant receiver | Receiver/PartyID?/ComponentID | Receiver/CommunicationComponent/TypeID=Constant/Value |
| Read response | IntegratedConfigurationReadResponse | IntegratedConfiguration750ReadResponse |

두 builder를 분리한다. 750 timeout 뒤 legacy Create로 자동 fallback하면 중복 mutation과 semantic 차이가 발생한다. capability/WSDL fingerprint를 계획에 고정한다.

| ESR/논리 참조 | Directory 목적지 |
|---|---|
| source SI name/namespace | IntegratedConfigurationID.InterfaceName/InterfaceNamespace |
| source SI SWCV | InboundProcessing.SenderInterfaceSoftwareComponentVersion |
| sender component/party | IntegratedConfigurationID.SenderComponentID/SenderPartyID |
| sender channel | InboundProcessing.CommunicationChannel |
| source operation 이름 | ReceiverRule/ReceiverInterfaceRule.Operation |
| OM name/namespace/SWCV | ReceiverInterfaceRule.Mapping |
| target SI key | ReceiverInterfaceRule.Interface[]·OutboundProcessing.ReceiverInterface |
| target component/party | receiver 결정·ReceiverInterfaces·OutboundProcessing 일치 |
| target channel | OutboundProcessing.CommunicationChannel |
| OM parameters | MappingParameters.Integer/String/Channel, 선언과 대조 |

XiReference를 그대로 SOAP에 넣지 않고 실제 Active refs/key에서 projection한다. ICO에는 보통 OM을 연결하며 MM은 OM 내부 program이다. operation은 내부 XiKey string이 아니라 이름이다. SWCV는 optional이어도 모호성 제거를 위해 계획에 넣는다. ICO key 자체에는 별도 SWCV 필드가 없다.

SCHEMA_ONLY 합성 ICO750 Body다. 원본과 같은 XSD 구조이며 HTTP/권한·업무 일관성·실행 성공은 검증하지 않았다.

~~~xml
<b:IntegratedConfiguration750CreateRequest xmlns:b="http://sap.com/xi/BASIS">
  <ChangeListID>11111111-1111-1111-1111-111111111111</ChangeListID>
  <IntegratedConfiguration>
    <MasterLanguage>EN</MasterLanguage>
    <IntegratedConfigurationID>
      <SenderPartyID/><SenderComponentID>BS_EXAMPLE_SOURCE</SenderComponentID>
      <InterfaceName>SI_EXAMPLE_OUT</InterfaceName>
      <InterfaceNamespace>urn:example:readiness</InterfaceNamespace>
    </IntegratedConfigurationID>
    <InboundProcessing>
      <SenderInterfaceSoftwareComponentVersion>22222222-2222-2222-2222-222222222222</SenderInterfaceSoftwareComponentVersion>
      <CommunicationChannel>
        <PartyID/><ComponentID>BS_EXAMPLE_SOURCE</ComponentID>
        <ChannelID>CC_EXAMPLE_SENDER</ChannelID>
      </CommunicationChannel>
    </InboundProcessing>
    <Receivers>
      <ReceiverWildcardIndicator>false</ReceiverWildcardIndicator>
      <ReceiverRule>
        <Operation>opExample</Operation>
        <Receiver><CommunicationComponent>
          <TypeID>Constant</TypeID><Value>BS_EXAMPLE_TARGET</Value>
        </CommunicationComponent></Receiver>
      </ReceiverRule>
      <NoReceiverBehaviour>Error Message</NoReceiverBehaviour>
    </Receivers>
    <ReceiverInterfaces>
      <Receiver><PartyID/><ComponentID>BS_EXAMPLE_TARGET</ComponentID></Receiver>
      <ReceiverInterfaceRule>
        <Operation>opExample</Operation>
        <Mapping>
          <Name>OM_EXAMPLE</Name><Namespace>urn:example:readiness</Namespace>
          <SoftwareComponentVersionID>22222222-2222-2222-2222-222222222222</SoftwareComponentVersionID>
        </Mapping>
        <Interface>
          <Name>SI_EXAMPLE_IN</Name><Namespace>urn:example:readiness</Namespace>
          <SoftwareComponentVersionID>22222222-2222-2222-2222-222222222222</SoftwareComponentVersionID>
        </Interface>
      </ReceiverInterfaceRule>
      <QualityOfService>EO</QualityOfService>
    </ReceiverInterfaces>
    <OutboundProcessing>
      <Receiver><PartyID/><ComponentID>BS_EXAMPLE_TARGET</ComponentID></Receiver>
      <ReceiverInterface>
        <Name>SI_EXAMPLE_IN</Name><Namespace>urn:example:readiness</Namespace>
        <SoftwareComponentVersionID>22222222-2222-2222-2222-222222222222</SoftwareComponentVersionID>
      </ReceiverInterface>
      <CommunicationChannel>
        <PartyID/><ComponentID>BS_EXAMPLE_TARGET</ComponentID>
        <ChannelID>CC_EXAMPLE_RECEIVER</ChannelID>
      </CommunicationChannel>
    </OutboundProcessing>
  </IntegratedConfiguration>
</b:IntegratedConfiguration750CreateRequest>
~~~

legacy의 constant receiver는 다음 구조다. 전체 builder에는 wrapper와 Receivers type까지 legacy 계약을 적용한다.

~~~xml
<Receiver><PartyID/><ComponentID>BS_EXAMPLE_TARGET</ComponentID></Receiver>
~~~

1:1 시나리오는 sender channel·한 receiver·target SI·OM·receiver channel과 component/direction 일치를 요구한다. XSD optional을 이유로 업무 필수 관계를 생략하지 않는다. IDoc/RFC처럼 operation 모델이 다르면 가짜 operation 대신 별도 capability로 분리한다.
## AUT 11 ChangeList의 요청·응답

default CL을 가정하지 않는다. ID 생략으로 새 CL이 생길 수 있으므로 미래 mutation에 explicit CL ID를 넣고 반환 ID·owner·객체 목록을 대조한다. ESR CL과 Directory CL은 repository·ID·상태가 다르다.

| Operation | global root | 구조 | 응답 |
|---|---|---|---|
| Create | ChangeListCreateRequest | Name 등 | ChangeListCreateResponse |
| CheckContent | ChangeListCheckContentRequest | GUID simple content | LogMessageCollection |
| Activate | ChangeListActivateRequest | GUID simple content | LogMessageCollection |
| GetState | ChangeListGetStateRequest | GUID simple content | ChangeListGetStateResponse |
| GetObjectIdentifiers | ChangeListGetObjectIdentifiersRequest | GUID simple content | ChangeListGetObjectIdentifiersResponse |
| GetCacheState | ChangeListGetCacheStateRequest | GUID simple content | ChangeListGetCacheStateResponse |

다음 모두 SCHEMA_ONLY이며 가짜 GUID다. 현재 문서/프로토타입 작업에서 호출하지 않는다. Create는 실제 변경 목록 생성 operation이다.

~~~xml
<b:ChangeListCreateRequest xmlns:b="http://sap.com/xi/BASIS">
  <Name>EXAMPLE_ONLY_DO_NOT_SEND</Name>
</b:ChangeListCreateRequest>
~~~

아래 GUID는 root text이며 안에 ChangeListID child를 추가하지 않는다.

~~~xml
<b:ChangeListCheckContentRequest xmlns:b="http://sap.com/xi/BASIS">11111111-1111-1111-1111-111111111111</b:ChangeListCheckContentRequest>
~~~

~~~xml
<b:ChangeListActivateRequest xmlns:b="http://sap.com/xi/BASIS">11111111-1111-1111-1111-111111111111</b:ChangeListActivateRequest>
~~~

~~~xml
<b:ChangeListGetStateRequest xmlns:b="http://sap.com/xi/BASIS">11111111-1111-1111-1111-111111111111</b:ChangeListGetStateRequest>
~~~

~~~xml
<b:ChangeListGetObjectIdentifiersRequest xmlns:b="http://sap.com/xi/BASIS">11111111-1111-1111-1111-111111111111</b:ChangeListGetObjectIdentifiersRequest>
~~~

~~~xml
<b:ChangeListGetCacheStateRequest xmlns:b="http://sap.com/xi/BASIS">11111111-1111-1111-1111-111111111111</b:ChangeListGetCacheStateRequest>
~~~

저장 WSDL의 Body XSD는 10개 예제를 통과시켰다. local 자식을 qualified로 바꾸거나 legacy에 750 전용 receiver를 넣은 부정 사례6개는 거부됐다. 이 검사는 Envelope 전체·HTTP·TLS·인증·권한·업무 규칙을 검증하지 않는다. XSD-valid 빈 Channel Create를 자체 business validator는 거부해야 한다.

## AUT 12 secret·원형 DTO·ReadContext

표준 Directory Read의 password 공백은 실제 공백·미설정이 아니라 실제 secret을 확인하지 못한 UNKNOWN일 수 있다.

- 신규/clone은 secretRef를 별도 resolve한다. Read→새 key Create가 credential을 복제한다고 가정하지 않는다.
- 공식 Change의 blank password 승계와 신규 Create 의미를 구분한다.
- secret 삭제/빈값/생략 의미는 adapter/설치 시험 전 지원하지 않는다.
- 비교에는 secret reference+generation을 사용한다. 추측 공격 가능한 평문 secret hash를 만들지 않는다.
- unknown 두 개를 같은 secret이라고 판정하지 않는다.
- secret 전송에는 승인된 TLS endpoint를 사용한다. 수집을 위해 SAP TLS 설정을 임의 변경하지 않는다.
- 로그·frontend diff·Excel·계획 JSON·CLI·exception chain·SDK stdout을 sanitizer 경계로 관리한다.
- 현재 flat channel detail을 Create DTO로 재사용하지 않는다. Party·namespace·module·table·User/Active context를 잃을 수 있다.

공식 password 설명:
https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d24bcf42262b63e10000000a42189d/content.htm

## AUT 13 Python backend와 Java worker의 경계

다음 위치는 제안이며 현재 구현된 기능이 아니다.

~~~text
backend/app/domains/authoring/
  router.py models.py planner.py validator.py orchestrator.py repository.py
backend/app/integrations/sap_po/
  directory_authoring.py esr_bridge.py
java-esr-worker/
  pinned-sdk-profile protocol local-model read-adapter future-writer
frontend/src/domains/authoring/
  manifest editor graph preview validation diff execution journal
~~~

Python은 typed manifest·DAG·fingerprint·revision·권한·durable journal, Directory adapter는 WSDL별 typed SOAP·모든 응답 메시지 해석, Java worker는 registry/model/serialization·허용한 remote capability만 담당한다. SAP SDK를 frontend에 넣거나 임의 URL/class/method 실행 API를 만들지 않는다.

SDK 로그가 stdout에 섞이므로 전체 stdout=JSON 방식은 맞지 않다. 전용 통신로 또는 length framing과 schemaVersion/requestId/jobId/stepId/attemptId/길이 제한을 사용한다. 한 요청에 정확히 하나의 terminal response를 보장하고 중복·누락·oversized frame을 거부한다.

worker profile은 SID+principalRef+SDK fingerprint+config revision이다. credential은 CLI·영구 JSON 대신 backend secret 경계에서 공급하고 worker 수명·환경·메모리를 검토한다. 한 JVM에서 여러 서버/계정/SDK를 재초기화하지 않는다. credential 교체 시 cache invalidation을 명시한다.

제안 자체 API는 /api/v1/authoring 아래 plans, validations, executions, events, cancel, reconciliations다. SAP REST나 기존 구현 route가 아니다. 권한은 authoring:read/plan/execute/activate와 SID boundary로 나누고 channels:control을 재사용하지 않는다. prototype에는 plan/read만 노출한다.

순수 Python ESR wire·JPype는 검증하지 않았다. 현재 입증한 local ESR 모델 수단은 Java SDK이며 Python 중심 제품 설계와 전 계층 Python-only 검증은 다른 주장이다.

## AUT 14 durable journal·충돌·멱등성

DB는 애플리케이션 PostgreSQL이며 SAP DB가 아니다. 새 순번 migration으로 추가한다.

| 엔터티 | 최소 필드 |
|---|---|
| plan/revision | immutable manifest·normalizationVersion·digest·SDK/WSDL fingerprints |
| object node | logical ID·kind·complete key·context·action |
| ref binding | resolved/server-returned ref·base/current version·operation owner |
| execution/step | stage·status·dependencies·account/SID·start/end |
| attempt | append-only ID·operation·request digest·dispatch time·response 여부·sanitized outcome |
| repository CL | ESR/Directory 구분·ID·owner·state·object identifiers |
| object lease | complete scope/key·owner·expiry·fencing token |
| audit | actor·permission·revision·decision·evidence scope |

create/reuse/update_existing/clone은 명시적 action이고 자동 upsert가 아니다.

- create: Active/User/draft/CL complete key 충돌 검사. AlreadyExists면 강제 Change 대신 reconcile.
- reuse: 예상 active version/signature/fingerprint 일치 객체를 읽기만 함. edit/close/delete하지 않음.
- update_existing: Active/User base version·owner 보존, 정상 lock/edit 경로, 저장 직전 base 변경 재검사. Directory Change는 delta가 아니므로 전체 Restricted DTO 재구성.
- clone: sourceRef→targetRef map으로 DT/MT/SI operation/MM graph/UDF/archive/OM refs를 역할별 remap. 문자열 일괄 치환 금지. secret 복제는 별도.

자체 Idempotency-Key는 (actor,sid,purpose,key) unique+canonical request digest로 구현한다. 동일 key/내용은 동일 execution, 내용이 다르면409다. SAP exactly-once 보장이 아니다.

mutation 전 dispatch journal commit, 응답/readback 후 checkpoint commit을 한다. 사이 crash/timeout은 UNKNOWN_REMOTE_OUTCOME이다. restart 후 mutation을 바로 재전송하지 말고 알려진 CL/key/version으로 reconcile한다.

plan lock 외 complete object key lease·CAS/fencing token으로 중복 worker를 차단한다. local lease가 SAP lock을 대체하지 않는다. stale token worker의 후속 dispatch를 막고 다른 user/job의 lock을 빼앗지 않는다.

## AUT 15 실행 상태·재시도·취소

Plan DRAFT→VALIDATING→INVALID 또는 READY, SDK/WSDL/base version/입력 변경 시 STALE→새 revision 재검사다. logical READY와 remote write READY를 구분한다.

미래 실행 순서 제안은 다음이다. 서버에서 실제 검증한 save/check/compile/submit 순서가 아니며 sandbox에서 확정해야 한다.

~~~text
PRECHECKING
 -> ESR_PERSISTING
 -> ESR_CHECKING / ESR_COMPILING
 -> ESR_ACTIVATING
 -> ESR_ACTIVE_READBACK
 -> DIRECTORY_PERSISTING
 -> DIRECTORY_CHECKING
 -> DIRECTORY_ACTIVATING
 -> DIRECTORY_ACTIVE_READBACK
 -> CACHE_WAITING
 -> RUNTIME_READBACK
 -> COMPLETED or COMPLETED_WITH_WARNINGS
~~~

실제 객체 의존 순서는 DT→MT→SI/MM→OM이고 operation은 SI 내부다. context가 다르면 ESR CL도 여러 개일 수 있다. ObjectAccess.activate와 CL submit을 근거 없이 둘 다 호출하지 않는다. ESR+Directory 전체를 atomic transaction처럼 표시하지 않는다.

| 실패 | 판정·복구 |
|---|---|
| 연결 전 실패가 확실 | bounded retry·attempt 기록 |
| 전송 후 timeout/연결 유실 | UNKNOWN_REMOTE_OUTCOME, 먼저 CL/key/version 조회 |
| Create 응답 유실 | 새 CL/Create 무조건 반복 금지 |
| 저장 응답 성공/readback 불일치 | 후속 객체·활성화 차단 |
| 일부 객체만 성공 | 성공 key/version/CL 유지, 실패·미실행 의존 단계 보고 |
| ESR 활성 성공/Directory 실패 | ESR 유지·Directory 복구 계획. 자동 ESR delete/revert 금지 |
| Activate 응답 유실 | CL state+Active contents+cache 조회 후 판단 |
| 캐시 지연 | bounded 상태 조회, 재활성화/full refresh/채널 제어 우회 금지 |
| 다른 사용자 변경·version 충돌 | REQUIRES_REPLAN, 강제 overwrite/unlock 금지 |
| 사용자 취소 | 미전송 단계 중단. in-flight가 서버 rollback됐다고 해석하지 않음 |

예외 상태는 FAILED_PRECHECK, FAILED_WITH_DRAFTS, BLOCKED_BY_LOCK, BLOCKED_BY_CONFLICT, UNKNOWN_REMOTE_OUTCOME, RECONCILING, CACHE_DELAYED, REQUIRES_REPLAN을 구분한다. terminal 결과에 active 생성물·남은 draft/CL/lock·미완료 참조를 기록한다.

SOAP Query/Read가 POST여도 논리 read일 수 있다. transport retry에 POST 전체를 허용하지 말고 operation별 bounded read retry를 둔다. Check/compile의 side effect는 미확정이다. invalid credential/locked/expired-password는 영구 오류로 분류해 로그인 폭주를 막는다.

cleanup 기본은 보고·재조회다. 자신의 handle/draft/CL ownership이 입증되지 않으면 release/revert/delete하지 않는다. logout/session close가 모든 edit lock을 해제한다고 가정하지 않는다. worker kill·요청 취소는 결과 불명확 상태를 만들 수 있다.

## AUT 16 결과·Active·Cache 성공 판정

Directory HTTP200/Fault없음은 완전 성공 기준이 아니다. 일반 LogMessage와 모든 객체별 collection의 LogMessageItem을 보존하고 ID 없는 메시지도 버리지 않는다.

| SeverityCode | 의미 | 처리 |
|---|---|---|
| 1 | 정보 | 대상·내용 보존 |
| 2 | 경고 | 불완전 생성 가능, readback·정책 판단 |
| 3 | 객체 오류 | 해당 객체 실패 |
| 4 | 종료·호출 transaction rollback | 해당 웹서비스 호출 경계 실패 |
| missing/unknown | 불명확 | 원문 code 보존, 성공 기본값 금지 |

severity4를 ESR+Directory 전체 rollback으로 확대하지 않는다. warning2에도 채널 없는 ICO 등이 생성될 수 있다. 반환 CL·object key·readback을 함께 확인한다.

ESR에 Directory 숫자 규칙을 적용하지 않는다. CheckResult.getMaxSeverity/hasAtLeastSeverity/getMessageList, XiObjectRetValContainer의 object/CL/owner, IntegrationResult.getVersionConflicts/getCheckResult/getIsIntegrationComplete를 각각 수집한다. wrapper clearMsg 전에 저장한다. authentication/authorization/validation/missing-dependency/lock/version-conflict/serialization/compilation/transport/unknown-outcome을 구분한다.

Directory CL enum은 Open/Transportable/Closed/Consolidated/Unknown이다. 한 문자열만으로 활성 성공을 추측하지 않고 activation log+원하는 Active 내용으로 판정한다.

GetCacheState는 consumer별 NotificationState/RefreshState·CachedObject[]다. 상태는 New/In Process/Successful/Warning/Failed/Unknown이다. 빈 배열은 전부 성공이 아니다. 필요한 Adapter Engine consumer·두 상태·대상 객체를 확인한다. timeout은 CACHE_DELAYED이고 full refresh를 자동 호출하지 않는다.

ChannelAdmin 상태는 runtime 가시성과 현재 상태일 뿐 업무 메시지 전달·MM 변환 성공이 아니다. mapping unit test도 UDF/lookup 외부 효과가 있을 수 있어 순수 local fixture와 통합 시험을 분리한다.

## AUT 17 구현 묶음과 수용 기준

| ID | 작업 | 완료 조건 |
|---|---|---|
| AUT-P1 | manifest DTO·schema·DAG | 완전 예제 성공, 누락/순환/중복/kind/미지원 거부, SAP dispatch0 |
| AUT-P2 | preview·canonical digest·export/reload | QName·operation owner·MM/OM refs·Directory projection 보존 |
| AUT-P3 | pinned local Java worker | source/SDK/runtime pin, 7+13 재현, IPC/비밀값 경계 |
| AUT-R1 | Directory Active/User read | 배열·Party·namespace·table/module 원형 보존 |
| AUT-R2 | ESR resolve·무인 연결 | 최초 실패/만료/권한/단절/timeout 무GUI 분류 |
| AUT-W1 | 제한 sandbox ESR | 2DT/2MT/2SI/MM/OM save/readback·compile/check/activate 순서 입증 |
| AUT-W2 | sandbox Directory | 필수 속성·secret·module·경고·CL/cache·runtime side effect |
| AUT-F1 | crash/응답유실/충돌/취소 | 중복 mutation 없음·UNKNOWN/reconcile·남은 객체 표시 |
| AUT-U1 | 권한/UI/회귀 | SID/계정 경계·SDK 변경 재계획·기존 읽기 회귀 |

이 표의 제품 작업을 현재 구현·배포한 것이 아니다. 원래 guarded probe와 계약을 구현 시작 자료로 제공한다. BS-001~027/MD-001~052/OR-001~062의 141개 항목을 완료율로 계산하지 않는다.

원격 시험이 허용되면 SID·sandbox component/namespace/SWCV·계정·operation·객체 prefix/수·Adapter Engine/외부 연결 격리·cleanup ownership·중단/reconcile 조건을 고정한다. 문서 준비 요청을 운영 SAP 작성 허가로 확대하지 않는다.

필수 부정·회귀 시험:

- 같은 이름·다른 namespace/SWCV/Party, Active/User version 차이·모호한 ref.
- SI mode 전환의 response/fault 제거, duplicate operation·owner 유지.
- namespace path·반복 필드·필수 target 누락·unsupported conversion.
- serializer ERROR/NPE, ZIP timestamp 비결정성, object graph와 ESR XML/wire 구분.
- private setter 우회0, 미지원 UDF/lookup 기본 거부.
- global QName·local unqualified·순서·nil/생략/빈값.
- legacy/750 교차 DTO 거부, GUID root child 오류, XSD-valid 빈Create 거부.
- 동명 다른 namespace 속성·table row/column·module 순서/반복 보존.
- Read 빈secret을 clone 가능으로 처리하지 않음.
- 같은 Idempotency-Key/다른digest409, stale fencing token·동시 job 차단.
- dispatch journal 경계 crash·Create/Activate 응답 유실 후 조회·재조정.
- ESR 성공/Directory 실패 자동 delete/revert0, 취소 후 신규 dispatch0.
- unknown severity·ID없는 메시지·item별 부분 실패 보존.
- cache consumer 누락·빈배열·Warning/Failed/timeout 성공 기본값 금지.
- frontend/로그/계획/CLI/exception에 실제 endpoint·secret·ticket 없음.
- prototype에서 SAP writer·channel control·test message dispatch0.
- 기존 읽기·권한·SID 회귀 유지. 검사 편의상 app startup을 무조건 실행하지 않음.

## AUT 18 본사 반입 자료와 출처

| 자료 | 필요한 원본 |
|---|---|
| SDK | JNLP·45JAR·순서/크기/SHA/CRC·지원 검토 |
| 계약 | Directory4종 WSDL+import·fingerprint, 주소는 사내 전용 |
| local 검증 | GuardRunner/GuardSelfTest/Bootstrap/Model/Mapping source와 freshness |
| 증거 | 최종 probe JSON·기존 attempt·ledger·verification summary |
| fixture | 합성 XML10개·부정 사례·manifest·순수 mapping fixture |
| 도구 | runner·분석/ledger builder·QA·경로 재바인딩 기록 |
| 제품 | app revision·기존 dirty 상태·사내 변경·현재 domain/API 계약 |

공개 Markdown은 상세 계약·지침이며 artifact 패키지가 아니다. JAR·SAP decompiled body·실제 host/계정/business key·raw WSDL/HAR/Directory XML·message payload는 공개하지 않는다. 옛 절대경로 원본은 보존하고 RESEARCH_ROOT map을 별도 기록한다. 이식과 실제 원격 작성 시험을 구분한다.

공식 참고 문서는 계약 차이 확인용이며, 현 설치의 호출 성공 증거는 아니다.

- Directory programming interface: https://help.sap.com/saphelp_snc700_ehp04/helpdata/en/48/d127e1e1c60783e10000000a42189d/content.htm
- Directory ReadContext: https://help.sap.com/docs/SAP_NETWEAVER_750/d0a0a7cb51dc40529bfcac724dd05796/48d2695b0d7d035be10000000a42189b.html
- Directory severity: https://help.sap.com/docs/SAP_NETWEAVER_731/d0a0a7cb51dc40529bfcac724dd05796/48d24b4142262b63e10000000a42189d.html
- ChangeList: https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d2613e0d7d035be10000000a42189b/content.htm

## MGT 1 관리 수집은 서로 다른 원본으로 나눈다

CPA 현재 구성, 캐시 갱신 이력, 잡의 영속 설정, 실제 실행·SubTask, TREX 인덱싱, 메시지 보존 정책은 같은 source가 아니다. 44개 AS Java 지표가 이 내용을 모두 반환하지 않는다. 이 절은 `PROPOSED` 수집 설계와 원본 계약 조사 지침이며, 새로운 원격 수집 성공을 주장하지 않는다.

| 대상 | 확보한 근거 | 본사에서 확인할 다음 계약 | 먼저 제공할 수 있는 내용 |
|---|---|---|---|
| CPA landing | `/CPACache/monitor.jsp`에서 과거 401, 후속 인증 GET 200의 작은 HTML landing | 실제 구성·history 읽기의 경로·인증·필터·상한·노드 범위 | 연결·인증·landing 지원 상태. 아직 객체 0개나 정상 캐시로 판정하지 않음 |
| CPA Channel 구성 | NWA 제한 목록·정확한 ID 조회·런타임 단건 대조 | 현재 객체와 전체 인벤토리·노드·변경 이력의 구분 | 확인한 scope의 구성 필드 |
| AAE 작업 | Archive/Delete/Recover 요약·실행·SubTask·실행 노드 UI | 별도 읽기 API/설치 schema·시간·실행 키 | 계약 확보 후 최근 실행 결과·오류·미실행 |
| AF Scheduler | Active/Terminated, 일정, Type, 실행 횟수·최근/다음 실행·노드 UI | 이 family의 읽기 contract | 설정 활성과 실행 성공을 분리한 목록 |
| AS Java Scheduler | 공식 로컬 Java API와 초기 UI | 원격 JXBP/JMX 등의 설치 계약·가시성 | 아직 독립 수집 완료 아님 |
| TREX | 설정 화면·미연결/사용 불가 표시 | 실제 사용 의도·연결·queue/index 상태·읽기 contract | 미사용/미확인/오류 구분 |
| Message Retention | 특정 시나리오 규칙 화면에서 규칙 없음 | 전역 inbound/outbound 기본값·override·규칙의 유효 범위 | 확인된 정책만 표시, 미확인 기본값 유지 |

## MGT 2 CPA 호출과 UME에서 확인할 사항

### MGT 2.1 단계별 성공을 구분한다

`GET {PO_ORIGIN}/CPACache/monitor.jsp`는 확인된 진입 경로다. 응답이 HTML landing이라는 사실만으로 객체 API가 있다고 간주하지 않는다. 후속 조사에서 이 landing은 491-byte HTML·표 0개였다. 이 숫자는 과거 캡처의 관측값이며 현재 응답 길이 검증 상수가 아니다.

인증 검증을 할 경우 같은 origin의 세션 안에서 원본 응답의 status/content-type/title/허용된 링크만 확인한다. 다음 단계를 각각 독립 결과로 남긴다.

1. 네트워크 연결.
2. 인증 수락.
3. landing 파싱.
4. 제한된 객체 목록·정확한 ID 읽기.
5. 전체성·paging·중단 채널 포함 여부.
6. 갱신 이력 읽기.
7. 노드별 적용 상태.

UI에서 발견한 링크를 자동으로 모두 따라가지 않는다. `Refresh`, `Full Refresh`, `Delta`, lock 생성, cache update처럼 변경 가능성이 있는 동작을 읽기 probe에 넣지 않는다. `/CPACache/history.jsp` 등 과거 경로 후보는 이 문서에서 성공한 외부 API로 승인하지 않는다. 실제 설치의 읽기 operation을 확인한 뒤 allowlist에 추가한다.

### MGT 2.2 권한을 추측으로 보정하지 않는다

UME는 AS Java의 사용자·그룹·역할·action을 관리하는 User Management Engine이다. 일반적인 “백엔드 시스템을 사용할 수 없는 잠재적 이유” 팝업은 원인 목록이며 현재 장애의 진단 결과가 아니다.

초기 안내에 등장한 `xi_af_cpa_monitor`는 조사 대상 설치의 정확한 조회 role/action 이름으로 확정되지 않았다. 그 문자열이 없다고 새 역할을 만들거나 Full Refresh 역할을 대체 부여하지 않는다. 설치 버전·귀속 application/service·action·호출 principal·endpoint별 결과를 대조한다.

조사한 `SAP_XI_CPA_FULL_REFRESH`에는 `xi_af_cpa_cache_refresh_full`과 `logical_locking_create` 관련 action이 있었다. 이 역할은 읽기 전용 권한의 근거가 아니다. 역할 이름만으로 CPA monitor 읽기 성공을 보장하거나 권한을 자동 변경하지 않는다.

### MGT 2.3 구성과 런타임을 조인하는 규칙

- `configuration_store`, `runtime_cache`, `runtime_status`, `history`, `mirror`를 source role로 분리한다.
- 같은 object ID를 우선 사용하되 정규화 전·후 값을 보존한다. 같은 채널 이름+component+direction이 유일하다고 가정하지 않는다.
- CPA에 구성 객체가 있어도 채널이 STARTED/OK라는 뜻은 아니다.
- `Adapter Software Component Version` GUID는 어댑터 SWCV 식별자다. 채널 revision, 노드 반영 완료 또는 SAP 제품 SP로 대체하지 않는다.
- 일반 CPA lookup Java API와 NWA 화면의 포함 범위가 같다고 가정하지 않는다. stopped 채널 제외 사례가 알려진 메서드와 단건 UI 관찰을 혼합하지 않는다.
- 제한된 목록에 나타나지 않은 객체를 삭제됐다고 판단하지 않는다. 원본 전체성이 확인된 동일 scope의 수집에서만 부재를 비교한다.

## MGT 3 잡 수집의 최소 필드와 조사 순서

### MGT 3.1 공통 모델

다음은 자체 DTO 제안이며 SAP의 공통 Job 응답이 아니다.

```json
{
  "sid": "POX",
  "job_family": "aae",
  "source_job_id": "opaque-internal-key",
  "configured_active": null,
  "schedule": null,
  "source_timezone": null,
  "last_execution": {
    "source_execution_id": null,
    "started_at": null,
    "ended_at": null,
    "result": "unknown",
    "processed_count": null,
    "execution_node": null,
    "subtasks": []
  },
  "source_role": "history",
  "support": "unverified",
  "limitations": ["installation_read_contract_missing"]
}
```

`sid+job_family+source_job_id+원본이 정의한 scope`로 식별한다. 클러스터 작업이면 노드는 실행 속성으로 두며 실행 노드가 바뀔 때마다 다른 Job을 만들지 않는다. definition, schedule/task, execution, SubTask, execution log를 분리한다. 화면 rowspan 빈 셀은 상위 execution 값을 상속할 수 있어 독립 행으로 잘못 파싱하지 않는다.

### MGT 3.2 원격 계약 탐색

1. 본사 설치의 공식 service inventory와 기존 integration 설정에서 읽기 서비스를 먼저 찾는다.
2. WSDL과 read operation의 input/output·binding·caller scope를 확보한다. JXBP의 존재만으로 AAE/AF/AS Java 전부가 조회된다고 판단하지 않는다.
3. 공식 Scheduler의 `getJobDefinitions`, `getSchedulerTasks`, `getJobs`, `getJobStatus`, `getJobLog` 등 로컬 Java API 이름을 HTTP endpoint로 변환하지 않는다.
4. JMX를 검토할 때 실제 설치의 connector·client library·P4/TLS·ObjectName·attribute·권한·노드 범위를 확인한다. 임의 MBean `invoke`를 노출하지 않는다.
5. 끝까지 필요한 필드가 남는 경우에만 검증된 읽기 DB 또는 별도 SAP측 Java 조회 모듈을 독립 작업으로 검토한다. 새 모듈 배포는 이번 읽기 개선의 선행 조건이 아니다.

AAE Delete 실행 로그를 읽었다고 모든 기간의 정리가 완료됐다거나, `ACTIVE=1`이라고 현재 Running/Success라고 표시하면 안 된다. 다음 실행 시각도 원본의 timezone과 recurrence를 확인하기 전 계산하지 않는다.

## MGT 4 보존 정책과 TREX

`There are no rules`는 해당 시나리오 규칙 목록의 관측이다. 글로벌 보존 기본값이 없다는 뜻이 아니다. 문헌의 `xiadapter.inbound.persistDuration.default`, `xiadapter.outbound.persistDuration.default`는 원본 계약 확인 후보이며 현재 설치값이 아니다.

정책 DTO에는 방향·적용 범위·규칙 ID·우선순위·원문 단위·유효 시각·override·관측 시각을 넣는다. 확인되지 않은 기본값과 새 규칙을 섞어 유효 보존 기간을 계산하지 않는다. 메시지 행의 `PERSIST_UNTIL`은 저장된 만료 정보 후보이며 현재 정책·실제 삭제 시각과 같다고 가정하지 않는다.

TREX index retention, package transfer, reorganization, queue processing은 메시지 원본 보존과 별개다. 현재 미연결 화면을 보고 설치 부재·장애·미사용 의도 중 하나로 단정하지 않는다. 사용 여부가 확인되기 전 일상 장애 알림을 활성화하지 않는다. 색인·정리·연결 설정을 켜서 데이터를 만들지 않는다.

## MGT 5 DB 분석은 설치 schema가 준비된 뒤 진행한다

### MGT 5.1 확인한 문헌 이름과 한계

| 후보 | 확인 근거 | 이 이름만으로 제공하면 안 되는 내용 |
|---|---|---|
| `BC_MSG_JOB` | SAP nZDM 문헌의 `JOB_ID`, `ACTIVE` | 전체 잡 실행 이력·현재 Running·최근 성공·SubTask |
| `XI_AF_CACHE_UPDT` | KBA 공개 preview의 `UPDT_TIME`, `REF_ID`, `NODE_ID`, `OBJ_ID`, `OBJ_TYPE`, `EVENT`, `SEQ_NUM`, `OBJ_BYTE`, `FULLREFRESH` | 모든 노드 적용 성공·완전 history·시각 단위·event 사전 |
| `BC_MSG` | 영속 비동기 메시지 저장 설명 | 동기 메시지 포함 전역 업무 건수·채널 현재 상태 |
| `BC_MSG_VERSION` | 메시지 버전 저장 설명 | 버전 행 수와 실제 업무 처리 건수의 동등성 |
| `BC_MSG_LOG`, `BC_MSG_LOG_STAT` | 설정 의존 로그·통계 설명 | 모든 메시지 로그·payload·완전 보관 |
| `BC_MSG_AUDIT`, `BC_MSG_DUP_CHECK` | Audit 영속화·중복 확인 설명 | 모든 Audit 존재·실행 이력 전체 |
| KBA 3549157의 `XI_DIR*` 174개 | 문헌의 고유 테이블명 목록 | 현재 schema 존재·컬럼·join·SQL·기능 의미 |

KBA 목록에는 `BC_MSG*`, `XI_AF*`, `BC_JOB*`, TREX 계열이 없다. 전체 SAP PO DB catalog로 해석하지 않는다. 이 조사에서는 실제 SAP DB 연결·metadata 조회·SQL 실행을 하지 않았다.

### MGT 5.2 본사 읽기 계약 확인 절차

1. DBA가 지정한 DB 종류·schema·읽기 계정·허용 테이블·쿼리 부하 한도를 준비한다. 기존 HANA profile이 관리 테이블 권한도 가진다고 가정하지 않는다.
2. 설치 버전의 catalog 가시성을 먼저 확인한다. HANA `SYS.TABLES`, `SYS.TABLE_COLUMNS` 같은 metadata 계약도 해당 버전·권한에서 검증한다. 미노출과 부재를 구분한다.
3. 확인된 테이블명·컬럼·타입·nullable·키·인덱스·schema signature를 내부 registry에 등록한다.
4. 같은 시각·노드·필터의 NWA/API와 최소 행을 대조한다. timestamp 단위·timezone·상태 코드·보존 범위·중복을 검증한다.
5. 허용된 identifier만 조립하고 값은 bind parameter로 보낸다. `SELECT *`, 임의 SQL 입력, DDL/DML/프로시저, 전체 덤프를 제공하지 않는다.
6. 행·시간 구간·응답 크기·timeout·취소와 매번 연결 종료를 적용한다. `OBJ_BYTE` 같은 직렬화 객체·본문은 기본 제외다.
7. mirror/replica라면 원본 역할과 추출 시각·지연을 별도로 기록한다. stale mirror를 runtime과 동등하게 표시하지 않는다.

기존 HANA 메시지 Collector의 identifier 검증·bounded page 패턴은 재사용 후보지만 Oracle buffer·procedure·checkpoint의 commit 경계를 관리 수집에 전용하지 않는다. SAP DB 직접 쓰기는 모니터링이나 작성 자동화의 구현 방법이 아니다.

## MGT 6 자체 관측 저장과 UI 연결

### MGT 6.1 공통 envelope

```json
{
  "data": [],
  "meta": {
    "sid": "POX",
    "provider_id": "channel_status_http_v1",
    "contract_version": "sha256-of-installation-contract",
    "source_role": "runtime_status",
    "support": "supported",
    "collection_status": "not_collected",
    "freshness": "unknown",
    "health": "unknown",
    "last_attempt_at": null,
    "collected_at": null,
    "last_success_at": null,
    "source_time": null,
    "valid_until": null,
    "node_scope": "unknown",
    "query_window": null,
    "returned_count": null,
    "total_count": null,
    "completeness": "unknown",
    "is_demo": false,
    "limitations": ["server_global_total_not_provided"]
  }
}
```

이 예시는 첫 수집 전의 합성 DTO다. 실제 수집 결과가 아니다. 신규 API의 canonical enum·시각 규칙은 START 7을 따른다. collection·freshness·health·support·completeness는 각각 다른 축이다. 성공적인 읽기의 `0건`, 인증 실패의 빈 응답, 목록 잘림, 아직 수집하지 않음은 구분한다.

실패한 시도는 `last_success_at`을 전진시키거나 마지막 성공 데이터를 빈 정상값으로 덮어쓰지 않는다. 일부 필드만 새로 수집되면 필드별 snapshot generation·source·시각을 유지한다. 같은 값이 반복됐다는 이유로 stale이라고 판정하지 않고, 새 요청 성공과 원본 갱신 시각을 구분한다.

### MGT 6.2 저장 경계

현재 migration 번호와 기존 schema를 다시 확인한 뒤 새 순번을 추가한다. 다음은 제안된 저장 역할이며 아직 존재하는 테이블이라는 뜻은 아니다.

- capability/contract registry: provider별 지원 범위·schema SHA·검증 시각·한계.
- collection run: 시도·성공·실패·소요 시간·범위·오류 분류.
- successful snapshot: 마지막 성공값·유효 기간·완전성·generation.
- change event: 동일 key의 상태·허용 설정 변화와 전후 fingerprint.
- alert event/transition: 최초 발생·최근 관측·확인·복구·담당자·중복 키.
- lease: `(sid, provider, scope)`별 owner·만료·fencing. 초기 단일 scheduler 이후 다중 인스턴스 전에 구현.

SAP HTTP/P4 조회 중 DB transaction을 길게 유지하지 않는다. 조회가 끝난 뒤 snapshot·상태 변화·알림 전이를 짧은 자체 DB transaction으로 저장한다. lease가 만료된 worker의 뒤늦은 결과는 fencing으로 거부한다.

화면 GET은 저장된 결과를 읽는다. 사용자 수·탭 수만큼 SAP 호출을 늘리지 않는다. 수동 수집은 서버가 허용한 scope만 큐에 넣어 중복 병합한다. 기존 HANA→Oracle scheduler와 동일 provider를 이중 실행하는 신규 scheduler를 무심코 만들지 않는다.

### MGT 6.3 알림과 기대 운용 기준

- 중요 채널·업무·담당자·예상 운용 시간을 자체 설정으로 등록한다.
- 모든 STOPPED를 장애로 알리지 않는다. STARTED와 ChannelState 부재·ERROR·INACTIVE를 구분한다.
- 변화의 첫 관측·지속 조건·중복 억제·복구를 저장한다. 수집 실패를 대상 시스템 장애로 단정하지 않는다.
- 알림 `ack`·`resolve`는 DB에 저장하고 SID/역할 경계를 검사한다. 샘플 알림을 실시간 사건으로 섞지 않는다.
- 메시지 실패·채널 상태·지표 시각이 겹친다는 것은 상관관계다. 자동 원인 확정으로 표시하지 않는다.
- LLM 문맥은 허용된 source·관측 시간·완전성·익명화된 상태만 전달한다. SAP 계정·원본 XML·업무 본문·동적 URL은 전달하지 않는다.

## MGT 7 운영 시험과 완료 조건

| 시험 | 기대 결과 |
|---|---|
| 잘못된 인증·403·HTML 로그인·SOAP Fault | 원인을 분류하고 마지막 성공값을 보존 |
| HTTP 200+빈 지표 응답 | CPU 0/정상으로 변환하지 않음 |
| 신규 parser가 모르는 상태·누락 필드 | unknown/partial. Running/OK 기본값 금지 |
| 응답 상한·pagination 미확정 | `total_count=null`, completeness 제한 표시 |
| 두 화면 동시 접근 | 공유 snapshot 사용, SAP 호출 중복 억제 |
| scheduler와 수동 갱신 경합 | 동일 scope 중복 실행 차단 |
| lease 만료 후 늦은 응답 | stale worker commit 거부 |
| 원본 설정 SHA·WSDL 변경 | 계약 불일치 표시, 승인되지 않은 parser로 정상 처리 금지 |
| 정지 예정 시간·비중요 채널 | 운용 기준을 반영한 알림 판정 |
| 익명화·비밀값 canary | 로그·예외·fixture·API·LLM 문맥에 비밀값 부재 |
| 인증·네트워크 장애 복구 | 제한된 retry 이후 정상값 복원, 재로그인 폭주 없음 |

실서버 부하 시험의 호출 수·시간 구간·대상 SID를 먼저 정한다. 기존 NWA UI의 10초 poll을 외부 수집 권장 주기로 복사하지 않는다. 지표·채널·설정·상세 로그는 원본 비용과 갱신 주기가 달라 동일 주기를 강제하지 않는다. 세션·WSDL·cache·credential version 변경 시 무효화와 재초기화 범위를 분리해 검증한다.

## MGT 8 공개 1차 문헌과 해석 범위

아래는 조사에 사용한 공식·SAP 작성 자료다. 문헌의 버전·일반 설명과 실제 본사 설치 응답을 별도로 기록한다. SAP for Me 전체 본문이 필요한 KBA는 본사 권한으로 확인한다. 이 문서에 유료 원문을 복제하지 않는다.

- [SAP ChannelAdminServlet 공식 설명](https://help.sap.com/docs/SAP_NETWEAVER_750/0158596e99ae4f7386f5c302d343368c/4ba2862d182b63a3e10000000a42189c.html): status와 start/stop, 필터·로그 선택지 구분.
- [SAP 작성 메시지 읽기 설명](https://community.sap.com/t5/technology-blog-posts-by-sap/reading-messages-from-pi-system/ba-p/13144443): AdapterMessageMonitoring 목록·header·Audit의 일반 기능.
- [외부 JMX 모니터 수집](https://help.sap.com/docs/SAP_NETWEAVER_750/d829358fde5e4333a4ec77068fec93f8/e8462140b431dd5fe10000000a155106.html): 공식 외부 수집 절차. 본사 connector·ObjectName 실증과 별개.
- [RMI-P4 연결 설명](https://help.sap.com/docs/SAP_NETWEAVER_731/d829358fde5e4333a4ec77068fec93f8/64617cfb94845d468b0498b4b2c53d74.html): 구버전 보조 자료이며 현재 SDK·보안 설정 대체 근거가 아님.
- [Scheduler API의 원격·로컬 구분](https://help.sap.com/docs/SAP_NETWEAVER_750/d829358fde5e4333a4ec77068fec93f8/4a5f7aab277d21dae10000000a421937.html): 로컬 Java API를 원격 SOAP로 일반화하지 않음.
- [JXBP architecture](https://help.sap.com/docs/SAP_NETWEAVER_740/d829358fde5e4333a4ec77068fec93f8/4a64ed2948e12a0ae10000000a42189c.html): 설치된 외부 서비스의 범위·등록·가시성은 추가 확인.
- [KBA 2371318 공개 preview](https://userapps.support.sap.com/sap/support/knowledge/en/2371318): 캐시 갱신 관련 컬럼 이름의 제한된 근거.
- [KBA 3549157](https://me.sap.com/notes/3549157/E): 확보 당시 Version 2, released 2025-01-15의 `XI_DIR*` 이름 목록. 설치 schema와 컬럼 계약은 아님.
- [SAP nZDM Java 가이드](https://help.sap.com/doc/033e646c8dfe4de9a9ab99369eff8f44/CURRENT_VERSION_NZDM/en-US/nzdm_java_win_po.pdf): `BC_MSG_JOB`의 영속 활성 설정 문맥.
- [SAP 작성 메시지 저장 테이블 설명](https://community.sap.com/t5/technology-blog-posts-by-sap/introduction-of-the-tables-that-keep-message-related-data-in-the-database/ba-p/13187390): 일반 저장 구조. 실제 schema·업무 건수 의미는 별도 확인.

## REF 1 141개 구현 준비 항목 전체

원본 `RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/readiness-ledger.json`의 BS 27개·MD 52개·OR 62개를 보존했다. 상태는 2026-10-19 당시의 증거 분류다. 본사에서 새로 실행한 시험 결과가 아니다. 상태명·서버 검증 false·남은 시험을 함께 읽는다.

원본 `may_run_in_current_request`는 당시 조사 요청의 범위 표시이며 현재 SAP 쓰기 허가로 사용하지 않는다. 본 문서에서 구현 요구사항을 적었다는 사실도 이미 코드가 구현됐다는 뜻이 아니다. 원격 서버 검증이 false인 항목은 그대로 유지한다.

| 그룹 | 항목 수 | 범위 |
|---|---:|---|
| BS | 27 | SDK bootstrap·인증·클래스패스·세션 |
| MD | 52 | ESR 모델·참조·스키마·매핑·직렬화 |
| OR | 62 | Directory·실행 계획·상태·복구·제품 통합 |

### REF 1 BS Bootstrap

#### BS-001 Repository 전체 클래스패스 범위

- 원본 상태: `proven-local-scope`.
- 주장·요구 범위: Repository에 선언된 JAR 45개 전체가 보호 장치가 적용된 검증 코드의 클래스패스를 구성합니다. 최소 클래스패스임을 입증한 것은 아닙니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 최종 운영 작업기의 패키지·클래스·리소스 의존성 완결성 확인, 서버 패치 호환성 검증, 라이선스에 따른 배포 검토.
- 근거:
  - repository-acquisition.json
  - run_offline.py
  - probe-results/BootstrapProbe.json

#### BS-002 Java 8의 headless 로딩

- 원본 상태: `proven-local`.
- 주장·요구 범위: Java 8 포터블 런타임에서 선택한 속성·세션·등록부 클래스를 headless 모드로 성공적으로 로딩했습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 이를 더 최신 Java 버전이나 MM 전체 기능에 일반화해서는 안 됩니다.
- 근거:
  - runtime-acquisition.json
  - probe-results/BootstrapProbe.json

#### BS-003 일반 Properties 초기화

- 원본 상태: `proven-local`.
- 주장·요구 범위: AIIProperties.init(Properties)는 JNLP 어댑터나 Web Start 실행 없이 접두사가 붙지 않은 일반 속성 이름을 읽습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험: 원본 목록 비어 있음. 이것만으로 추가 시험 불필요를 뜻하지 않음.
- 근거:
  - probes/BootstrapProbe.java#property_init
  - probe-results/BootstrapProbe.json#property_init

#### BS-004 최초 속성 소스의 고정

- 원본 상태: `proven-static`.
- 주장·요구 범위: AIIProperties.init(PropertySource)는 INFO 진단 메시지를 출력한 뒤 후속 초기화를 무시하고 최초 속성 소스를 유지합니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 운영 작업기는 실행 중 프로필 교체를 시도하는 대신 변경 불가능한 서버·배포 프로필을 검증해야 합니다.
- 근거:
  - bootstrap-javap/com.sap.aii.utilxi.prop.api.AIIProperties.txt#init/configurationError

#### BS-005 빈 세션 위임 등록

- 원본 상태: `proven-local`.
- 주장·요구 범위: ClientSessionInformationProvider에 빈 CoreSessionInformationProvider 위임을 등록하는 데 성공했으며 hasSession은 false를 유지했습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험: 원본 목록 비어 있음. 이것만으로 추가 시험 불필요를 뜻하지 않음.
- 근거:
  - probes/BootstrapProbe.java#empty_session_delegate
  - probe-results/BootstrapProbe.json#empty_session_delegate

#### BS-006 로그인 서비스 메타데이터 등록

- 원본 상태: `proven-local`.
- 주장·요구 범위: JNDI 조회 없이 LoginService 싱글턴 생성과 Login·ObjectAccess·ChangeList bean 메타데이터 등록에 성공했습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 이들은 메타데이터 레코드이며 인증된 원격 인터페이스가 아닙니다.
- 근거:
  - probes/BootstrapProbe.java#login_service_metadata_only/register_metadata_*
  - probe-results/BootstrapProbe.json

#### BS-007 6개 인자 로그인 계약

- 원본 상태: `proven-static`.
- 주장·요구 범위: 인자 6개인 login의 매개변수 이름은 enteredUserName, password, newPassword, lang, data, logonTicket이며, 성공 경로에는 startAppAfterLogin 호출이 없습니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 최초 외부 인증은 아직 시험하지 않았으며, 오류 분기에서 GUI 재접속이 호출될 수 있습니다.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.LoginServiceImpl.txt#login(6):0..561

#### BS-008 newPassword의 null 조건

- 원본 상태: `proven-static`.
- 주장·요구 범위: 일반 비밀번호 로그인에서는 newPassword=null이어야 합니다. 빈 newPassword는 null이 아닌 char[]로 변환되어 PasswordChangeCallback에 제출될 수 있습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 비밀번호 만료·변경 필요 상태는 운영자의 명시적 조치가 필요한 오류로 처리하고 대체 비밀번호를 임의 생성하지 않아야 합니다.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.EJBHomeFactory$PwChangeHandler.txt#constructor:17..29/handle:106..132

#### BS-009 null 비밀번호의 위험

- 원본 상태: `proven-static`.
- 주장·요구 범위: 비밀번호 콜백 생성자는 password.toCharArray를 호출하므로 일반 비밀번호 모드에서 null 비밀번호는 안전하지 않습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험: 원본 목록 비어 있음. 이것만으로 추가 시험 불필요를 뜻하지 않음.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.EJBHomeFactory$PwChangeHandler.txt#constructor:9..14

#### BS-010 사용자 이름 정규화 순서

- 원본 상태: `proven-static`.
- 주장·요구 범위: enteredUserName.trim() 전에 사용자 이름을 sessionUsername으로 복사하고, sessionUsername을 initRemoteFactory에 전달합니다. 호출자는 호출 전에 값을 검증하고 앞뒤 공백을 제거해야 합니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험: 원본 목록 비어 있음. 이것만으로 추가 시험 불필요를 뜻하지 않음.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.LoginServiceImpl.txt#login(6):0..23,353..361

#### BS-011 티켓·비밀번호 인증 선택

- 원본 상태: `proven-static`.
- 주장·요구 범위: logonTicket != null이고 LoginUtil.isSSOenabled()인 경우에만 티켓 핸들러를 선택하며, 나머지 경우에는 비밀번호 핸들러를 생성합니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 인증 모드 하나를 명시적으로 사용하고 티켓·자격 증명 값을 로그나 영속 작업 계획에 기록하지 않아야 합니다.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.EJBHomeFactory.txt#connect:31..84

#### BS-012 로그인 언어의 원격 계약

- 원본 상태: `unverified-remote-contract`.
- 주장·요구 범위: Language를 LoginServiceBI.login에 전달하지만 null 허용 여부는 입증하지 못했습니다. getInstalledLanguages는 설정된 로그인 언어를 읽습니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 실제로 설정된 목록에서 Language를 선택한 뒤 별도로 승인된 읽기 전용 시험에서 인증해야 합니다.
- 근거:
  - bootstrap-evidence.json#LoginServiceImpl.getInstalledLanguages/login

#### BS-013 hasSession과 인증 성공의 구분

- 원본 상태: `proven-static`.
- 주장·요구 범위: 원격 factory 연결 전에 클라이언트 세션 객체를 설치합니다. 로컬 hasSession=true는 인증 성공을 입증하지 않으며, 확인한 실패 경로는 이 값을 해제하지 않습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 원격 호출 성공 후에만 명시적인 인증 완료 상태를 기록하고 실패한 작업기 프로세스는 폐기해야 합니다.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.LoginServiceImpl.txt#login(6):143..160,353..428

#### BS-014 GUI에 종속된 재접속

- 원본 상태: `proven-static-blocker`.
- 주장·요구 범위: ReconnectProcessor는 Swing Application·EDT와 ReconnectDialog에 의존하며, executeReconnect는 애플리케이션을 시작하는 login 오버로드를 사용합니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 비대화형 오류 처리·재인증 경로를 구현하고 입증해야 하며 login(6)을 선택하는 것만으로는 충분하지 않습니다. 비즈니스 프록시용 공개 BeanProxyProvider 훅은 있지만, 선택해 확인한 클래스에서는 LoginService 싱글턴 교체용 setter를 찾지 못했고 최초 _login은 해당 프록시 훅을 우회합니다.
- 근거:
  - bootstrap-evidence.json#ReconnectProcessor.checkIsReconnectPossible/getReconnectPassword/executeReconnect
  - bootstrap-javap/com.sap.aii.ib.clsif.login.ReconnectProcessor.txt
  - bootstrap-evidence.json#LoginServiceProvider.registerBeanProxyProvider/BeanAccessHandler

#### BS-015 최초 로그인 오류의 GUI 진입

- 원본 상태: `proven-static-blocker`.
- 주장·요구 범위: 최초 _login의 예외 처리도 BeanAccessHandler.onReconnectRequired → LoginService.reconnect → GUI 재접속 경로로 진입할 수 있습니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 연결 거부, 유휴 세션 만료, 권한 오류, 서버 재시작, 응답 유실 상황에서 GUI 없이 처리되는지 입증해야 합니다.
- 근거:
  - bootstrap-evidence.json#LoginServiceImpl._login
  - bootstrap-evidence.json#BeanAccessHandler.handleRemoteExInBusinessMethod/handleRuntimeExInBusinessMethod

#### BS-016 logout의 정리 범위

- 원본 상태: `proven-static`.
- 주장·요구 범위: LoginService.logout은 서버 로그아웃 후 원격 factory를 닫지만 로컬 클라이언트 세션이나 원격 인터페이스 캐시를 직접 비우지 않습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 정리·재사용 의미는 별도로 시험해야 합니다. 프로필별 프로세스 분리는 이러한 전역 상태가 초기화된다고 가정하지 않게 해 줍니다.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.LoginServiceImpl.txt#logout:0..102

#### BS-017 ContextCleaner 종료 대기

- 원본 상태: `proven-static`.
- 주장·요구 범위: closeInitialContext는 데몬 ContextCleaner를 시작하고 isAlive 확인 없이 10000ms 동안 join합니다. 완료 로그만으로 종료를 입증할 수 없습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 작업기 종료 시간 제한과 리소스 해제 관찰.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.EJBHomeFactory.txt#closeInitialContext:0..58

#### BS-018 요청 timeout 미확인

- 원본 상태: `unresolved-bounded-static-search`.
- 주장·요구 범위: 확인한 LoginServiceImpl·EJBHomeFactory·ReconnectProcessor 메서드에서는 호출별 로그인·읽기·쓰기 timeout 설정을 찾지 못했습니다. 10초 정리 대기는 요청 timeout이 아닙니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 배포된 P4 broker의 연결·읽기·호출 timeout 설정을 추적하고, 프로세스 실행 기한 초과 후 결과 불명 상태를 처리하는 방식을 시험해야 합니다.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.clsif.login.LoginServiceImpl.txt
  - bootstrap-javap/com.sap.aii.ib.clsif.login.EJBHomeFactory.txt
  - bootstrap-javap/com.sap.aii.ib.clsif.login.ReconnectProcessor.txt

#### BS-019 프로세스 전역 상태와 동시성

- 원본 상태: `proven-static`.
- 주장·요구 범위: LoginService, ClientSessionInformationProvider, 원격 factory, ServiceBase 등록부는 프로세스 전역 상태입니다. getBusinessInterface 캐시는 공유 Map이며 해당 메서드는 동기화되어 있지 않습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 작업기 하나 안의 작업을 순차 실행하고 서버·배포·계정 프로필을 분리해야 합니다. 다중 사용자 스레드 안전성을 입증한 것은 아닙니다.
- 근거:
  - bootstrap-evidence.json#LoginServiceProvider/ClientSessionInformationProvider/EJBHomeFactory/ServiceBase/LoginServiceImpl.getBusinessInterface

#### BS-020 RMI 프로토콜과 라우터 설정

- 원본 상태: `proven-static`.
- 주장·요구 범위: RMI 프로토콜이 잘못되었거나 없으면 P4로 대체됩니다. DebugRouterData는 endpoint와 라우터 동작을 재정의할 수 있습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 실제 JNLP 프로토콜·포트를 검증해야 합니다. HTTP 포트에 산술식을 적용해 P4 포트를 추정하거나 보안 전송을 알림 없이 낮추지 않아야 합니다.
- 근거:
  - bootstrap-evidence.json#EJBHomeFactory.getProtocol/connect

#### BS-021 타입 등록과 GUI startup 분리

- 원본 상태: `proven-static`.
- 주장·요구 범위: IFR·Mapping 등록에는 공개 로컬 진입점이 있습니다. 전체 GUI startup은 원격 래퍼, 개인화 설정, 리스너, GUI 서비스까지 등록합니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 입증된 최소 모델 등록 범위는 모델 검증 코드를 참조해야 하며 GUI main이나 startup 전체를 호출하지 않아야 합니다.
- 근거:
  - bootstrap-evidence.json#IfrTypeRegistration/MappingTypeRegistration/StartupCodeEntry

#### BS-022 XML·Java 직렬화의 구분

- 원본 상태: `proven-static`.
- 주장·요구 범위: ESR XML serializer와 Java/RMI 객체 그래프 직렬화는 서로 다릅니다. BeanProxy는 Java 직렬화 검사를 수행하며, XML serializer 등록만으로 전송 호환성을 입증할 수 없습니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 구성한 모델 그래프를 로컬에서 직렬화·역직렬화하고 승인된 통합 시험에서 실제 EJB 전송 계약을 검증해야 합니다.
- 근거:
  - bootstrap-evidence.json#SerializationServiceProvider/BeanProxy.serializeObject

#### BS-023 BeanProxy의 패키지 제한

- 원본 상태: `proven-static`.
- 주장·요구 범위: BeanProxy의 로컬 직렬화 검사가 실행되면 기본 금지 패키지 목록이 GUI·client·clsif 패키지 객체 인스턴스를 거부합니다. 검사는 조건부이며 항상 작동하는 서버 필터로 입증된 것은 아닙니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - payload 모델 그래프에 editor·controller·client service 객체를 연결하지 말고 모델 데이터와 참조만 포함해야 합니다.
- 근거:
  - bootstrap-evidence.json#BeanProxy.<clinit>/BeanProxy$1

#### BS-024 초기화 중 차단된 부수 동작

- 원본 상태: `proven-local-side-effect`.
- 주장·요구 범위: 로컬 초기화에서 네이티브 jperflib 로딩과 GUID 초기화용 로컬 호스트 DNS 조회를 시도했습니다. 거부 보호 장치가 두 동작을 모두 차단했으며 bootstrap 전체 단계는 완료되었습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 이를 대체 경로가 있는 초기화 부수 동작으로 해석해야 합니다. SAP 네트워크 호출 성공이나 네트워크 시도가 전혀 없었다는 증거로 해석해서는 안 됩니다.
- 근거:
  - probe-results/BootstrapProbe.json#guard_events.denied_details

#### BS-025 원격 변경 미실행 범위

- 원본 상태: `unverified-remote-contract`.
- 주장·요구 범위: 이번 작업에서는 로그인, 원격 조회, create, update, edit, activation, submit, logout, 채널 제어, SAP 설정 변경을 실행하지 않았습니다.
- `blocks_production_external_authoring`: `true`.
- 남은 구현·시험:
  - 원격 성공·권한·호환성에 관한 모든 주장은 명시적으로 이번 시험 범위 밖에 있습니다.
- 근거:
  - probes/BootstrapProbe.java
  - probe-results/BootstrapProbe.json
  - probes/GuardRunner.java

#### BS-026 중복 서비스 등록의 덮어쓰기

- 원본 상태: `proven-static`.
- 주장·요구 범위: ServiceBase 중복 등록은 경고를 기록하며, 이후 registerServiceImpl이 Map 항목을 교체합니다. 이는 상태를 깨끗하게 초기화하는 수단이 아닙니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 결정적인 등록 순서를 고정하고 JVM 하나에서 구·신 배포 클래스나 provider를 혼합하지 않아야 합니다.
- 근거:
  - bootstrap-javap/com.sap.aii.ib.core.service.ServiceBase.txt#checkIfAlreadyRegistered/registerServiceImpl

#### BS-027 startup 없는 애플리케이션 식별

- 원본 상태: `proven-local`.
- 주장·요구 범위: Repository 전체 클래스패스를 사용하면 startup 없이 애플리케이션 식별 getter를 평가할 수 있습니다.
- `blocks_production_external_authoring`: `false`.
- 남은 구현·시험:
  - 인증 전에 REPOSITORY_WSCLIENT인지 확인해야 합니다. 다른 클래스패스는 자동 역할 탐색 결과를 바꿀 수 있습니다.
- 근거:
  - probe-results/BootstrapProbe.json#application_identity_without_startup

### REF 1 MD ESR 모델과 매핑

#### MD-001 XSD QName·schema·다중도 복제

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - XSD local type name, target namespace, primitive QName, minOccurs=0 and maxOccurs=unbounded survived cloneSchema.
- 관측값: {"namespace":"urn:local-readiness:20261019","type":"DT_Source","min":"0","max":"unbounded","type_kind":2}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - ESR이 허용하는 XSD 부분집합·제한 조건, import·참조 DT, 서버 활성화 검사.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json","pointer":"#/records/0/result/MD-001.schema_clone"}

#### MD-002 XiKey와 가상 SWCV context

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - XiKey.NAME/NAMESPACE and context are created by factories; object ID is unassigned and version is null.
- 관측값: {"name":"DT_Source","namespace":"urn:local-readiness:20261019","key_elements":["DT_Source","urn:local-readiness:20261019"],"context":"WKV 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 실제 SWCV·workspace 해석과 create가 반환하는 객체·version·ChangeList 식별자.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json","pointer":"#/records/0/result/MD-002.key_context"}

#### MD-003 DT schema와 MT의 DT 참조

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - TypeService-created DT accepts schema; MT.setDataType preserves the DT XiReference.
- 관측값: {"dt":{"name":"DT_Source","namespace":"urn:local-readiness:20261019","key_elements":["DT_Source","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"mt":{"name":"MT_Source","namespace":"urn:local-readiness:20261019","key_elements":["MT_Source","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"dt_link":{"name":"DT_Source","namespace":"urn:local-readiness:20261019","key_elements":["DT_Source","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"schema_complex_types":1}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 중첩·교차 SWCV DT 참조, 실제 payload namespace 기본값, 서버 검사.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json","pointer":"#/records/0/result/MD-003.dt_mt_links"}

#### MD-004 SI 내부 operation과 요청 MT

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - SI.createOperation builds an inner operation whose owner is SI; request MT reference survives.
- 관측값: {"si":{"name":"SI_Source","namespace":"urn:local-readiness:20261019","key_elements":["SI_Source","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"operation":{"name":"SI_Source.process","namespace":"urn:local-readiness:20261019","key_elements":["SI_Source.process","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"operation_names":["process"],"request":{"name":"MT_Source","namespace":"urn:local-readiness:20261019","key_elements":["MT_Source","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"mode":"A"}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 다중 operation 인터페이스, 중복 이름, RFC·IDoc, 비문서형 인터페이스 변형.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json","pointer":"#/records/0/result/MD-004.si_inner_operation"}

#### MD-005 SI mode setter의 부수 효과

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - Changing synchronous to asynchronous removes response; a subsequent async response setter rejects the assignment.
- 관측값: {"response_removed":true,"async_response_exception":"com.sap.aii.ibrep.bom.ifr.InconsistentDefinitionException","request_preserved":true}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 모든 인터페이스 pattern·category·mode 조합, fault와 best-effort 동작.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json","pointer":"#/records/0/result/MD-005.mode_link_side_effect"}

#### MD-006 OM operation·MM 참조와 1:1

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - OM source and target links point to SI operations; MM request-program link and SDK 1:1 multiplicity are retained.
- 관측값: {"source_operation":{"name":"SI_Source.process","namespace":"urn:local-readiness:20261019","key_elements":["SI_Source.process","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"target_operation":{"name":"SI_Target.process","namespace":"urn:local-readiness:20261019","key_elements":["SI_Target.process","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"request_mm":{"name":"MM_Local","namespace":"urn:local-readiness:20261019","key_elements":["MM_Local","urn:local-readiness:20261019"],"context":"ID: 00112233445566778899aabbccddeeff","version_specifier":"null","object_id_assigned":false},"multiplicity":"1:1","derived_message_links":"explicitly configured; remote MappingAnalysis not called"}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - MappingAnalysis resolver, 매개변수·속성 바인딩, category 도출, 서버 일관성.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json","pointer":"#/records/0/result/MD-006.om_links_multiplicity"}

#### MD-007 5종 모델의 Java 직렬화 복원

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - DT/MT/SI/MM/OM local object graph is Java-serializable; refs and SI inner-owner identity survive readback.
- 관측값: {"object_count":5,"bytes":14198,"sha256":"f7014d4c60c415e0d3d8bf909ff1caffc3453da2f054749dc10552da2c436dfc","identity_and_links_preserved":true,"scope":"Java object-graph bytes only; not wire envelope/server acceptance or ESR XML serialization"}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - BeanProxy 전송 envelope·금지 패키지 필터링, 클래스 호환성, 원격 수용 여부.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json","pointer":"#/records/0/result/MD-007.java_serialization_roundtrip"}

#### MD-008 Node·Brick·Pin 직접 그래프

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - A source PinOut is linked to a destination PinIn in a MappingGroup; node cardinality is retained.
- 관측값: {"source_path":"/value","target_path":"/value","source_context":"","group_bricks":2,"destinations":1,"source_min":"0","source_max":"unbounded"}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 서로 다른 중첩·반복 context, 필수 target root 의미, 매핑 실행.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/result/MD-008.low_level_graph"}

#### MD-009 그래프 XML 복원과 새 노드 해석

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - Serializer/load agents preserve a direct link and resolve source/destination identities against fresh Node trees.
- 관측값: {"xml_bytes_utf8":199,"xml_sha256":"fd2473f7943a62bb82701f5a6c1210fb513c78161b629e5f7f42732fa6f2bafb","xml_root":"brick","source_path":"/value","target_path":"/value","source_context":"","load_protocol_items":0}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 함수 그래프 노드, namespace 충돌, 변수·공유 group 그래프, context 변경.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/result/MD-009.graph_xml_roundtrip"}

#### MD-010 XSD 기반 Node QName·다중도

- 원본 상태: `locally_verified`.
- 로컬 확인 사실:
  - XsdDocSchema/TreeDoc constructs namespace-qualified field nodes with 0..unbounded multiplicity; own path resolves.
- 관측값: {"root":"","field_path":"/ns0:Source/ns0:value","field_namespace":"urn:local-readiness:source","min":"0","max":"unbounded","find_own_path":true}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 모호한 로컬 이름, attribute, choice, 재귀, import, sequence 순서, suppress 의미.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/result/MD-010.xsd_tree"}

#### MD-011 V2V UDF 서명·코드 XML 복원

- 원본 상태: `locally_verified_with_limitations`.
- 로컬 확인 사실:
  - Public getSignature mutation, one argument, execution type and code survive FLib XML serialization/load.
- 관측값: {"key":"localIdentity","exec_type":0,"arguments":1,"results":1,"xml_sha256":"15c9014ac54290fbd7596d9fcb9cc0510058e7347b765350bbe81d324a140c01","xml_bytes_utf8":413,"load_protocol_items":0,"not_tested":"UDF graph binding/Java compile/execution/server persistence"}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - UDF 그래프 바인딩, 컴파일, 실행, C2C·Q2Q, 라이브러리 의존성, 매개변수 바인딩.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/result/MD-011.udf_model_xml_roundtrip"}

#### MD-012 headless 기능 매핑 metadata 복원

- 원본 상태: `locally_verified_with_limitations`.
- 로컬 확인 사실:
  - Public functional serializers produce loadable Project XML/metadata ZIP and equal generated Java after roundtrip.
- 관측값: {"source_path":"/ns0:Source/ns0:value","target_path":"/ns1:Target/ns1:value","project_xml_sha256":"4c1b30015811744175f4fb02b16bff58e3abb841f460b5bcd68ba85a645c007c","metadata_bytes":803,"metadata_sha256":"73260eec4ad365519c38a444b20890d62d835d82477217943a97bc3cf711881d","metadata_entries":["metadata"],"java_chars":2878,"java_sha256":"469cd9dc6eecda279a9121800d20d7e320c0e83c300bad95c1d52f7d25dc25e6","java_equal_after_roundtrip":true,"feedback":["startLoading","loaded"],"serializer":"public functional content serializers; optional UI view state excluded","compiled_or_executed":false}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 전체 GUI customization·view 상태, 값이 있는 매개변수, 재사용 라이브러리, 런타임 컴파일, 서버 수용 여부.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/result/MD-012.project_headless_roundtrip"}

#### MD-013 MM 참조·schema·그래프·source 통합

- 원본 상태: `locally_verified_with_limitations`.
- 로컬 확인 사실:
  - XiTransformation retains MT refs, schema, graph ZIP, generated source/class identity, JDK and structure properties through Java serialization.
- 관측값: {"java_serialized_bytes":9895,"java_serialized_sha256":"2f04956a2a754f2bb7ab0993c2858e3261ef297d51be93747d51805aef1460aa","program_name":"_MM_Local_","package":"com.sap.xi.tf","source_structure_type":"zip","target_structure_type":"zip","metadata_sha256":"914fdb987d4f903ed6c1668620298fb961440b4870d2322aa2f3c4bebef58899","source_java_sha256":"11aeeb7c7f902f6e2f0855cda0a3b390845630b285a94fb4c7af75acea62e75d","source_message":"MT_Source","target_message":"MT_Target","source_field":"/ns0:MT_Source/ns0:value","source_property_file":"Source.xsd","compiled_jar_present":false,"scope":"synthetic in-memory refs/schema/graph/metadata/source/JDK/container only; no remote acceptance"}
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 원격 create·update·다시 읽기, 서버 컴파일·검사·활성화, 실제 업무 payload 결과.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/result/MD-013.mm_complete_local_roundtrip"}

#### MD-014 타입 bootstrap 전 메모리 속성 설정

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Use the actual allowlisted JNLP property names, including com.sap.aii.ib.client.applicationname.repository.
  - Initialize AIIProperties before registries to avoid default profile-file fallback.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 운영 환경·속성 계층화와 업그레이드 호환성.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/2/methods/6","class":"com/sap/aii/utilxi/prop/api/AIIProperties","method":"init"}

#### MD-015 타입·직렬화·링크 등록부

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Common IFR and repository IFR registration plus mapping type, serialization and link registration are required.
  - Missing registerLinkService raised TypeNotRegisteredException for XI_TRAFO during source MT link assignment.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 버전별 등록부 수명주기와 분리된 작업의 동시 실행.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/35/methods/9","class":"com/sap/aii/ib/bom/mapping/MappingTypeRegistration","method":"registerLinkService"}

#### MD-016 key·context·version 식별자 분리

- 원본 상태: `design_constraint`.
- 구현 요구사항:
  - Use symbolic dependency IDs in JSON and a separate registry of actual XiReferences returned by SAP.
  - Never substitute the synthetic probe SWCV GUID or manufacture server object/version/ChangeList identifiers.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 실제 동일·교차 workspace 참조 해석과 정규화.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/14/methods/2","class":"com/sap/aii/ib/bom/gen/XiKey","method":"getNameInstance"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/19/methods/1","class":"com/sap/aii/ib/bom/gen/XiReference$Factory","method":"getInstance"}

#### MD-017 TypeService의 언어·context 초기화

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Use newInstance(key, context, Language) to establish original/loaded language and version context.
  - Do not treat new DataType(key) alone as the complete initialized model.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 한국어·영어 텍스트, master·original 언어, 번역된 문서의 다시 읽기.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/21/methods/5","class":"com/sap/aii/ib/bom/gen/TypeServiceImpl","method":"newInstance"}

#### MD-018 ESR이 허용하는 XSD 부분집합

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - Validate datatype name/type alignment, namespace/form rules, global/type restrictions and schema node constraints.
  - A successful Java setter or schema clone is not evidence that ESR activation accepts a schema.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 순수 검사기의 fixture 행렬과 지원하는 XSD 구문에 대한 서버 일관성 검증.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/101","class":"com/sap/aii/ibrep/bom/ifr/SchemaChecks$SchemaUploadChecker","method":null}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/104","class":"com/sap/aii/ibrep/bom/ifr/SchemaChecksHelper$LocalNamespaceUnqualifiedChecker","method":null}

#### MD-019 DT 중첩 참조와 schema 정규화

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - setSchema rebuilds TYPE/UI links and schema imports/includes; preserve the resulting links/context.
  - Use the referenced DT QName and actual dependency reference, not an arbitrary copied schema label.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 동일·교차 namespace DT 재사용, 동일·교차 SWCV context, 재귀, import DT 연결.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/31/methods/2","class":"com/sap/aii/ibrep/bom/ifr/XiObjectWithSchema","method":"setSchema"}

#### MD-020 cardinality 표기·상호 제약 검증

- 원본 상태: `unverified_edge_case`.
- 구현 요구사항:
  - Distinguish numeric occurrence bounds from the unbounded token.
  - Validate min <= max, absent/default behavior and bad lexical values before touching mutable SDK models.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - -1, 0, 숫자가 아닌 값, 공백, 매우 큰 경계값, min>max, 잘못된 unbounded minimum.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/13/methods/23","class":"com/sap/aii/utilxi/xsd/api/XsdElement","method":"setMinOccurs"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/13/methods/26","class":"com/sap/aii/utilxi/xsd/api/XsdElement","method":"setMaxOccurs"}

#### MD-021 MT 식별자와 XML payload root 분리

- 원본 상태: `design_constraint`.
- 구현 요구사항:
  - Track ESR MT key namespace separately from XML payload namespace.
  - Build MM message roots from the resolved MT payload identity and DT content, not a display label.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - null·기본 payload namespace, 명시적 대체 namespace, 서버 생성 schema와의 비교.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/32/methods/2","class":"com/sap/aii/ibrep/bom/ifr/MessageType","method":"setDataType"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/32/methods/4","class":"com/sap/aii/ibrep/bom/ifr/MessageType","method":"setXMLPayloadNS"}

#### MD-022 null setter의 링크 제거 의미

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - Represent omitted JSON field versus explicit link removal separately.
  - Construct/validate a fresh candidate model before applying changes to an existing mutable object.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - patch 의미와 기존 객체의 다시 읽기, 전체 링크 setter의 null·빈 배열 동작.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/32/methods/2","class":"com/sap/aii/ibrep/bom/ifr/MessageType","method":"setDataType"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/38/methods/1","class":"com/sap/aii/ib/bom/mapping/MapLinkUtil","method":"setLinks"}

#### MD-023 부모 factory 기반 operation key

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Operation is an SI inner object; use createOperation/getOperation and the returned operation reference.
  - Observed SI_Source.process key is not a license to concatenate names manually for every object type.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 구분자·Unicode·길이 경계값, 중복 이름, operation 제거, 다중 operation 참조.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/33/methods/17","class":"com/sap/aii/ibrep/bom/ifr/ServiceInterface","method":"createOperation"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/24/methods/1","class":"com/sap/aii/ib/bom/ifr/IfrKeyComputation","method":"getOperationKey"}

#### MD-024 SI setter 순서와 허용 조합

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - Set SI category/pattern/document orientation, then operation pattern/mode, then MT references.
  - Recompute references after changing mode or style; response removal was verified.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - STATELESS·XI30COMPATIBLE·STATEFUL·TUCC, 동기·비동기·best-effort, document-oriented·type-oriented 조합.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/34/methods/1","class":"com/sap/aii/ibrep/bom/ifr/Operation","method":"setOperationMode"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/33/methods/6","class":"com/sap/aii/ibrep/bom/ifr/ServiceInterface","method":"setIsDocumentOriented"}

#### MD-025 Fault 타입과 링크 변경 부수 효과

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - FaultMessageType has distinct XiTypeId constants; do not assume every fault reference is a normal MT.
  - setFaultMessages removes existing FAULT links before checking fault permission; prevalidate on a clone.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - fault 객체 구성, 허용 category·mode, fault-to-fault 매핑, 실패 시 복구.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/16","class":"com/sap/aii/ib/bom/gen/XiTypeId","method":null}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/34/methods/19","class":"com/sap/aii/ibrep/bom/ifr/Operation","method":"setFaultMessages"}

#### MD-026 OM 대상의 SI·operation 구분

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - OUTBOUND_IF/INBOUND_IF role links reference SI operation identities in the tested model.
  - Preserve ordered indexes and do not replace them with the plain SI display name.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 다중 operation, RFC·IDoc 인터페이스 형식, SWCV 의존성을 넘는 operation 선택.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/36/methods/23","class":"com/sap/aii/ib/bom/mapping/Mapping","method":"getSourceIterfaces"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/36/methods/25","class":"com/sap/aii/ib/bom/mapping/Mapping","method":"getTargetInterfaces"}

#### MD-027 OM 방향·category·message 도출

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - Source/target operation selection drives request/response/fault message links and mapping category.
  - MD-006 set the derived message links explicitly; it did not execute the remote resolver.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - resolver 입력·읽기 전용 서버 조회, 정상 OM과 비교한 전체 일관성 검증.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/106/methods/1","class":"com/sap/aii/ibrep/core/mapping/MappingAnalysis","method":"determineAndAddMessageLinksAndCategory"}

#### MD-028 message 다중도와 필드 반복 구분

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - 1:1 refers to message parameters and must not be inferred from a payload field being 0..unbounded.
  - Store source/target parameter indexes and min/max values and derive multiplicity using the SDK.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 1:n·n:1·n:m, 배열 생략, 비연속 위치, multi-message schema·wrapper 의미.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/105/methods/1","class":"com/sap/aii/ibrep/core/mapping/util/Multiplicity","method":"determineMultiplicity"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/44","class":"com/sap/aii/ib/bom/mapping/SplitMergeAttributes$Parameter","method":null}

#### MD-029 OM 프로그램 순서와 속성 바인딩

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - Request/response/fault programs include ordered XiReferences and matching PropertySets.
  - setRequestProgramLinks alone only demonstrates links, not complete parameter binding.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 값이 있는 속성, container 매개변수, 다중 transformation, 다중도 정리.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/36/methods/7","class":"com/sap/aii/ib/bom/mapping/Mapping","method":"setRequestPrograms"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/42","class":"com/sap/aii/ib/bom/mapping/ProgramWithPropertySet","method":null}

#### MD-030 QName 기반의 모호하지 않은 필드 선택

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - Node.getPureName is an editor path token and may include a prefix; use XName local-name plus namespace.
  - The probe searches one unique field; production must use full qualified path segments and reject ambiguities.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 서로 다른 부모·namespace 아래의 반복 local name, prefix, attribute, 재귀 확장.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/58/methods/42","class":"com/sap/aii/ib/gui/xmleditor/doc/Node","method":"getPureName"}

#### MD-031 Pin 인자 방향과 그래프 소유권

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Connect destination input to source output and add the source brick to the destination MappingGroup.
  - Do not recreate DestBrick indiscriminately: its constructor replaces a previously attached destination.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 순환, 공유 source 그래프, 다중 입력 pin, 연결을 잃지 않는 기존 매핑 편집.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/76/methods/4","class":"com/sap/aii/mappingtool/mf/tvd/PinIn","method":"setLink"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/80/methods/16","class":"com/sap/aii/mappingtool/mf/tvd/bricks/DestBrick","method":"setGroup"}

#### MD-032 context·반복에 따른 매핑 의미

- 원본 상태: `unverified_edge_case`.
- 구현 요구사항:
  - Preserve source context node, usedAs/asXML settings, hierarchy and target root-generation semantics.
  - A preserved graph link and equal generated Java are not proof of correct business transformation output.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 중첩 반복, 선택적 부모 누락, createIf, useOneAsMany, removeContexts, suppress, queue 경계.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/79/methods/9","class":"com/sap/aii/mappingtool/mf/tvd/bricks/SrcBrick","method":"setContext"}

#### MD-033 MM의 참조·내용 표현 일관성

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Keep MT references, zipped source/target schemas, graph metadata, generated source, JDK and additional metadata aligned.
  - MD-013 verified combined local serialization; references remain synthetic and unresolved by SAP.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 실제 MT·DT 생성 schema를 대상으로 한 저장·다시 읽기와 서버 compiler·일관성 검증.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/46/methods/4","class":"com/sap/aii/ib/bom/mapping/XiTransformation","method":"getSourceMessages"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/45/methods/38","class":"com/sap/aii/ib/bom/mapping/XiMapping","method":"serializeTransientProperties"}

#### MD-034 MM 기반 Java 클래스·package 생성

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Populate IDataAccess class properties from mm.getProgramName()/getPackageName(), plus the correct test/temp suffixes.
  - The tested MM_Local yields _MM_Local_ in com.sap.xi.tf; do not accept arbitrary class identity from untrusted JSON.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - Unicode·Java 식별자가 아닌 매핑 이름, namespace별 중복 객체 이름, 구버전의 명명 규칙.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/98/methods/27","class":"com/sap/aii/mappingtool/fwutil/api/DataAccessAbstract","method":"getClassName"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/45/methods/26","class":"com/sap/aii/ib/bom/mapping/XiMapping","method":"getProgramName"}

#### MD-035 UDF 공개 구성 API 보정

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - FunctionDefinition.setSignature is private; use the signature initialized by the constructor via public getSignature().
  - Set argument/result/parameter definitions and execution type through that object; never bypass visibility.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 표준 함수의 복제·재사용 의미와 전체 UDF 그래프·source 생성.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/48/methods/18","class":"com/sap/aii/ib/bom/flib/FunctionDefinition","method":"getSignature"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/48/methods/37","class":"com/sap/aii/ib/bom/flib/FunctionDefinition","method":"setSignature"}

#### MD-036 UDF 실행 타입·source 코드 구분

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - Preserve V2V=0/C2C=1/Q2Q=2; ARGUMENT/RESULT/PARAMETER definitions, JavaType and library identity.
  - Treat source body and parameter bindings separately; this task never compiled or executed UDF code.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - C2C·Q2Q result list, 다중 출력, init·cleanup·global 구역, 외부 import.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/51","class":"com/sap/aii/ib/bom/flib/MethodSignatureDefinition","method":null}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/52","class":"com/sap/aii/ib/bom/flib/MethodArgDefinition","method":null}

#### MD-037 IDataAccess의 상속 계약

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Implement inherited IDbTableAccessor.getDbTabDefinitions even for an empty map.
  - Provide schemas, feedback, class properties, serialization agents, parameter proxy, JDK and workspace; reject external/execute stubs in the offline path.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 해당 기능을 명시적으로 활성화할 때의 library reader와 DB·RFC lookup plugin.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/64","class":"com/sap/aii/mappingtool/api/IDataAccess","method":null}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/65","class":"com/sap/aii/mappingtool/api/IDbTableAccessor","method":null}

#### MD-038 Project.save와 선택적 UI 상태 결합

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - Direct Project.save/getMetaData logged a swallowed NullPointerException because MappingTool GUI was absent.
  - The tested alternative uses public functional serializers and omits optional presentation view state; it does not initialize a GUI.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 향후 서버에서 다시 읽은 뒤 사용자 지정 값이 있는 상태의 보존과 정상 GUI 재로딩 동작.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/63/methods/42","class":"com/sap/aii/mappingtool/Project","method":"save"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/71/methods/9","class":"com/sap/aii/mappingtool/mf/MTMemento","method":"saveState"}

#### MD-039 기능 metadata writer의 범위

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - Serialize function storage, transformation, test data, empty customization and parameter container using public serializers.
  - Emit mappingtool version XI7.1 and ZIP member metadata; load through SDK before accepting output.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 값이 있는 customization, template, 재사용 라이브러리, Project.save의 지원 버전별 차이.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probes/MappingProbe.java","symbol":"functionalMetadata/metadataZip"}

#### MD-040 MM 매개변수·transient 속성

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - Serialize additional metadata after setting structure properties, JDK and container; restore transient properties on load.
  - Only an empty parameter container was tested; do not claim parameterized mapping support.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 값이 있는 import·export 매개변수, channel 매개변수, JavaType, 기본값, OM PropertySet 바인딩.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/45/methods/38","class":"com/sap/aii/ib/bom/mapping/XiMapping","method":"serializeTransientProperties"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/45/methods/39","class":"com/sap/aii/ib/bom/mapping/XiMapping","method":"deserializeTransientProperties"}

#### MD-041 컴파일 전 상태의 null JAR

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Generated source/metadata are distinct from compiled bytecode; null JAR mirrors the observed prepareSave step.
  - Report source built / checked / compiled / activated / runtime deployed as separate outcomes.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 서버 컴파일 트리거, 저장·활성화 후 bytecode 제공 여부, 실제 매핑 시험 결과.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/99/methods/2","class":"com/sap/aii/mappingtool/fwutil/api/ViewUtil","method":"prepareSave"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/45/methods/3","class":"com/sap/aii/ib/bom/mapping/XiMapping","method":"setJar"}

#### MD-042 JDK compliance와 라이브러리 의존성

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - Use the client/server-supported JDKCompliance model and preserve imported archives/function-library references.
  - JDK18 in a model does not verify the server compiler, Java APIs or archive compatibility.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 정확한 서버 Java·SP compiler 버전, 금지 API, UDF archive, 의존성 버전 충돌.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/47","class":"com/sap/aii/ib/bom/mapping/JDKCompliance","method":null}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/45/methods/54","class":"com/sap/aii/ib/bom/mapping/XiMapping","method":"setUsedJars"}

#### MD-043 XIM import의 MT 식별자 교체

- 원본 상태: `static_contract`.
- 구현 요구사항:
  - An imported mapping graph is not sufficient evidence that original ESR MT identities are retained.
  - Restore actual source/target XiReferences and compare schemas after import rather than treating .xim as a server create request.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 유효성이 알려진 XIM 입력, import mode 차이, import 후 MT 참조·다시 읽기 검사.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/mm-evidence.json","class":"com/sap/aii/ibrep/gui/mapping/xitrafo/action/ImportMapCommand","method":"createSourceAndTargetRefs"}

#### MD-044 증거 hash와 의미 기반 중복 판별

- 원본 상태: `design_constraint`.
- 구현 요구사항:
  - SDK Project.getMetaData creates a ZipEntry without setting a fixed timestamp in the observed method.
  - The custom probe metadata entry uses setTime(0); other blobs/serialization still need canonical semantic comparison.
  - Use byte hashes for evidence integrity and normalized object/spec/reference fingerprints for duplicate detection.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 프로세스·시간·순서 변경에 따른 반복 생성과 그래프·참조의 결정적 정규화.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/63/methods/15","class":"com/sap/aii/mappingtool/Project","method":"getMetaData"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probes/MappingProbe.java","symbol":"metadataZip"}

#### MD-045 원격 payload에서 GUI 객체 제외

- 원본 상태: `design_constraint`.
- 구현 요구사항:
  - Transfer domain models/core references/blobs, not Project, Node, Swing components or IDataAccess objects.
  - Successful unrestricted local ObjectOutputStream does not exercise BeanProxy forbidden-package policy.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 네트워크 없이 실제 serializer로 정확한 wrapper envelope와 모델 전용 그래프를 검사.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/17","class":"com/sap/aii/ib/bom/gen/XiObject","method":null}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probes/ModelProbe.java","symbol":"MD-007.java_serialization_roundtrip"}

#### MD-046 실제 ESR 내용 기반 schema 해석

- 원본 상태: `unverified_server_contract`.
- 구현 요구사항:
  - For existing MTs resolve DT dependencies/SWCV and generated payload schema before constructing graph nodes.
  - Do not generate a schema from MT name alone when payload namespace, imported definitions or external references differ.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 추이적 DT 참조를 포함한 실제 MT schema의 읽기 전용 해석과 editor 결과 비교.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/31/methods/1","class":"com/sap/aii/ibrep/bom/ifr/XiObjectWithSchema","method":"getSchema"}

#### MD-047 저장 후 생성 참조 대조·보정

- 원본 상태: `unverified_server_contract`.
- 구현 요구사항:
  - Record each server returned object/reference and update pending dependents before their persistence.
  - The synthetic local references have no assigned object ID/version; they prove local identity representation only.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 실제 create·update 응답 구조, 임시 key, 저장 후 참조의 다시 읽기.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/17/methods/12","class":"com/sap/aii/ib/bom/gen/XiObject","method":"getObjectReference"}

#### MD-048 앱 경계에서의 검증 원자성

- 원본 상태: `design_constraint`.
- 구현 요구사항:
  - Setters can remove old links before validating/replacing them; build a new candidate/clone and validate all references first.
  - Keep original read model and candidate separate; SDK mutation failure must not corrupt the tool preview.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 지원하는 전체 update 작업의 setter 실패 행렬과 복제본 비교.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/34/methods/19","class":"com/sap/aii/ibrep/bom/ifr/Operation","method":"setFaultMessages"}
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/classes/38/methods/1","class":"com/sap/aii/ib/bom/mapping/MapLinkUtil","method":"setLinks"}

#### MD-049 단일 비동기 직접 필드 MVP

- 원본 상태: `design_constraint`.
- 구현 요구사항:
  - Initial support matrix should cover DT/MT, stateful-free SI async request, one source/target MM direct field and OM 1:1.
  - Expose fault, sync, multimap, UDF execution, reusable library and parameterized scenarios only after their own validations.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 분리된 개발 서버에서 create·check·compile·activate·다시 읽기와 payload 매핑 시험의 성공.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/result/MD-013.mm_complete_local_roundtrip"}

#### MD-050 경고의 명시적 분류

- 원본 상태: `locally_verified_with_limitations`.
- 구현 요구사항:
  - New in-memory Project logs Received metadata is null; classify it as empty initial metadata, not silent corruption.
  - Earlier swallowed MTMemento NPE was a separate defect in the direct UI-oriented save route and is retained in attempts.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 패키징된 작성 작업기의 예상하지 못한 오류 로그 0건과 경고 허용 목록.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/stdout_other"}

#### MD-051 SAP 클래스 초기화 전 오프라인 보호

- 원본 상태: `locally_verified`.
- 구현 요구사항:
  - Run only behind the restrictive root-owned guard before loading SAP classes.
  - GUID initialization attempted hostname resolution and PerfTimes attempted native jperflib; both were blocked before side effects.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 운영용 sandbox·격리 설계. 이 Java 8 SecurityManager 시험 장치를 일반적인 sandbox 완전성의 근거로 사용해서는 안 됩니다.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/MappingProbe.json","pointer":"#/records/0/guard_events"}

#### MD-052 클라이언트 build·version 계약

- 원본 상태: `design_constraint`.
- 구현 요구사항:
  - Pin and hash actual installation JNLP resources, preserve ordered classpath and record SDK/compiler/runtime versions.
  - Avoid mixing SP/patch client jars or inferring support from Java public access alone.
- `remote_persistence_verified`: `false`.
- 남은 구현·시험:
  - 지원 버전 행렬, 통제된 업그레이드 차이 분석, 지원 가능한 배포·라이선스 입장.
- 근거:
  - {"file":"RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/models-evidence.json","pointer":"#/source_jars"}

### REF 1 OR 실행 조정과 Directory

#### OR-001 생성·저장·편집잠금·활성화·설정변경·Start/Stop를 현재 실행하지 않는다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 생성·저장·편집잠금·활성화·설정변경·Start/Stop를 현재 실행하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-001","acceptance":"Mock transport spy로 금지 operation dispatch 0건, planned API execution=false 상태를 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-002 BASIS wrapper qualified/local child unqualified 직렬화를 보존한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: BASIS wrapper qualified/local child unqualified 직렬화를 보존한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-002","acceptance":"향후 serializer 출력이 saved XSD와 일치하고 default namespace 오류를 거부하는 회귀 테스트를 추가한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-offline-validation.json

#### OR-003 SOAP 1.1 document/literal 및 단일 공통 SOAPAction을 사용한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: SOAP 1.1 document/literal 및 단일 공통 SOAPAction을 사용한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-003","acceptance":"가짜 HTTP transport에서 exact Content-Type/SOAPAction/operation wrapper와 timeout을 캡처한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json

#### OR-004 short-host alias는 기존 명시적 rewrite를 재사용하고 endpoint scope를 제한한다

- 원본 상태: `IMPLEMENTATION_GAP`.
- 주장·요구 범위: short-host alias는 기존 명시적 rewrite를 재사용하고 endpoint scope를 제한한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-004","acceptance":"허용 alias/외부 schema/redirect/absolute endpoint spoofing 분리 fixture로 대상 origin을 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/integrations/sap_po/client.py
  - PROJECT_ROOT/backend/app/core/config.py

#### OR-005 채널 Create와 ICO Create는 최소 1개라는 업무 검증을 별도 적용한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: 채널 Create와 ICO Create는 최소 1개라는 업무 검증을 별도 적용한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-005","acceptance":"XSD상 empty Create 허용과 자체 모델 422 거부를 동시에 테스트한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-offline-validation.json

#### OR-006 필수값·min/maxOccurs·nil/empty/omission·enum·길이를 type별로 검증한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: 필수값·min/maxOccurs·nil/empty/omission·enum·길이를 type별로 검증한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-006","acceptance":"Component/Channel 60경계·GUID형식·Language2·protocol10·nil거부·sequence/중복 필드 부정 fixture를 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json

#### OR-007 Channel raw DTO의 Namespace·table row/cell·모듈 순서·parameter group 연결을 보존한다

- 원본 상태: `IMPLEMENTATION_GAP`.
- 주장·요구 범위: Channel raw DTO의 Namespace·table row/cell·모듈 순서·parameter group 연결을 보존한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-007","acceptance":"동명다른Namespace/반복모듈/다중행테이블/필수Parameter 배열을 serialize-readback round-trip한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - PROJECT_ROOT/backend/app/domains/channels/service.py

#### OR-008 Read 모델과 Restricted Create/Change 모델을 구분한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: Read 모델과 Restricted Create/Change 모델을 구분한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-008","acceptance":"Read 전용 admin 값 제거 및 optional Read.AdapterMetadata가 없을 때 Create readiness를 차단한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json

#### OR-009 어댑터별 기술필드·의존 조건·secret·engine·모듈·인증서 사전조건을 catalog로 관리한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: 어댑터별 기술필드·의존 조건·secret·engine·모듈·인증서 사전조건을 catalog로 관리한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-009","acceptance":"허용된 향후 read 범위에서 정상 채널과 adapter metadata의 기술 키/방향별 필수 조건을 대조한다","scope":"future_readonly","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - PROJECT_ROOT/backend/app/domains/channels/service.py

#### OR-010 legacy ICO와 ICO750 receiver 모델을 분리한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: legacy ICO와 ICO750 receiver 모델을 분리한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-010","acceptance":"서비스별 builder round-trip과 750 ReceiverWildcardIndicator/Extractor를 legacy에 넣는 부정 fixture를 유지한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-offline-validation.json

#### OR-011 sender SI key와 SWCV를 ICO Header/InboundProcessing에 각각 projection한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: sender SI key와 SWCV를 ICO Header/InboundProcessing에 각각 projection한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-011","acceptance":"fake resolved XiReference에서 sender key와 SWCV GUID projection이 서로 다른 필드에 생성되는지 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/model-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-012 ICO Mapping에는 OM DesignObjectID를 넣고 MM 직접 연결을 거부한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: ICO Mapping에는 OM DesignObjectID를 넣고 MM 직접 연결을 거부한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-012","acceptance":"MM logical ID를 Mapping에 지정하면 type mismatch로 거부하고 OM/SI signature fixture를 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/model-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-013 SI 내부 OPERATION XiKey와 Directory Operation 문자열을 구분한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: SI 내부 OPERATION XiKey와 Directory Operation 문자열을 구분한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-013","acceptance":"multi-operation SI에서 송신 operation 이름과 ESR inner reference를 별도 값으로 보존한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/model-evidence.json

#### OR-014 receiver component·party·SI·channel이 모든 ICO 영역에서 일치해야 한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: receiver component·party·SI·channel이 모든 ICO 영역에서 일치해야 한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-014","acceptance":"ReceiverInterfaces/OutboundProcessing/Channel key의 다른 party 또는 component fixture를 각각 거부한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-015 Mapping parameter 이름/타입/값과 lookup channel 참조를 일치시킨다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: Mapping parameter 이름/타입/값과 lookup channel 참조를 일치시킨다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-015","acceptance":"Integer/String/Channel parameters의 누락·형식·source signature를 fake model로 검사하고 실제 읽기 형식은 후속 대조한다","scope":"future_readonly","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/model-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/mm-evidence.json

#### OR-016 logical ID와 실제 key/context/version/SWCV/CL를 별도 reference registry에 보존한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: logical ID와 실제 key/context/version/SWCV/CL를 별도 reference registry에 보존한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-016","acceptance":"server-returned ref 변경 fixture가 후속 MT/SI/MM/OM 및 active ref projection까지 전달되는지 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/model-evidence.json

#### OR-017 new/reuse/update/clone을 자동 upsert 없이 명시한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: new/reuse/update/clone을 자동 upsert 없이 명시한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-017","acceptance":"동일 key의 active-only/draft-only/타인lock/다른내용/equal 재사용을 각 정책으로 판정한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - https://help.sap.com/saphelp_snc700_ehp04/helpdata/en/48/d127e1e1c60783e10000000a42189d/content.htm?no_cache=true
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-018 clone은 role link·inner operation·DT XSD·MM graph·OM program을 각각 remap한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: clone은 role link·inner operation·DT XSD·MM graph·OM program을 각각 remap한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-018","acceptance":"복합 fixture의 source namespace가 의도된 외부 dependency 외에는 target 생성물에 남지 않는지 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/model-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/mm-evidence.json

#### OR-019 기존 객체의 active/draft/version/owner를 snapshot하고 stale plan을 거부한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 기존 객체의 active/draft/version/owner를 snapshot하고 stale plan을 거부한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-019","acceptance":"계획 후 base version 변경·draft owner 변경·WSDL hash 변경 시 execution 전에 STALE을 반환한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - https://help.sap.com/docs/SAP_NETWEAVER_750/d0a0a7cb51dc40529bfcac724dd05796/48d2695b0d7d035be10000000a42189b.html
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-020 확인된 로컬 Java bootstrap·모델 object-graph 직렬화와 미검증 원격 인증·wire 수용을 구분한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: 확인된 로컬 Java bootstrap·모델 object-graph 직렬화와 미검증 원격 인증·wire 수용을 구분한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-020","acceptance":"로컬 bootstrap 7항목·모델 7항목은 확인됐다. 원격 인증·session/service 획득은 향후 읽기 범위에서 검증하고 ESR XML/wire envelope와 서버 수용·저장은 별도 허용된 sandbox에서 검증한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 추가 로컬 검증: {"bootstrap_semantic_checks_passed":7,"model_semantic_checks_passed":7,"java_object_graph_roundtrip_verified":true,"esr_xml_serializer_verified":false,"remote_authentication_verified":false,"server_wire_acceptance_verified":false,"scope":"root guarded local probes; not Java runs performed by this subtask"}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/BootstrapProbe.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/probe-results/ModelProbe.json

#### OR-021 DT→MT→SI/MM→OM 의존 순서와 서버 반환 ref 갱신을 따른다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: DT→MT→SI/MM→OM 의존 순서와 서버 반환 ref 갱신을 따른다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-021","acceptance":"순서가 뒤집힌 fake transport, 응답ref 변동, dependency missing을 주입하여 후속 dispatch를 차단한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/model-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json

#### OR-022 매핑 그래프 저장·generated source·compiled artifact·활성화를 구분한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: 매핑 그래프 저장·generated source·compiled artifact·활성화를 구분한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-022","acceptance":"순수 1:1 fixture의 metadata/source 저장 후 compiler 응답/compiled artifact/active 결과를 명시된 sandbox에서 검증한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/mm-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json

#### OR-023 CheckResult/IntegrationResult의 warning·conflict·completion을 판정한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: CheckResult/IntegrationResult의 warning·conflict·completion을 판정한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-023","acceptance":"각 return container의 success 객체+error 메시지/충돌/완료false 조합을 fake DTO로 테스트한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json

#### OR-024 ObjectAccess.activate와 CL submit을 같은 API로 취급하지 않는다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: ObjectAccess.activate와 CL submit을 같은 API로 취급하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-024","acceptance":"승인된 향후 sandbox에서 GUI 동등 흐름의 check/compile/submit/activate 중 실제 필요한 순서와 중복호출 효과를 검증한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json

#### OR-025 ESR/Directory 및 다른 context의 CL ID/owner/state를 분리한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: ESR/Directory 및 다른 context의 CL ID/owner/state를 분리한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-025","acceptance":"동일 형식 GUID라도 repository 또는 SWCV가 다르면 잘못된 step 연결을 거부한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-026 Directory mutation마다 explicit CL을 넣고 반환 ID/owner를 확인한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: Directory mutation마다 explicit CL을 넣고 반환 ID/owner를 확인한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-026","acceptance":"mock 응답의 CL 누락/다른 ID/다른 owner를 불명확 또는 오류로 판정하고 다음 mutation을 차단한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d2613e0d7d035be10000000a42189b/content.htm?no_cache=true
  - https://help.sap.com/saphelp_snc700_ehp04/helpdata/en/48/d127e1e1c60783e10000000a42189d/content.htm?no_cache=true

#### OR-027 편집 lock·소유 변경 목록·재사용 read handle을 구분한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: 편집 lock·소유 변경 목록·재사용 read handle을 구분한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-027","acceptance":"별도 sandbox에서 타인lock/자기lock/재로그인/close/세션만료 효과와 exception accessor를 검증한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - https://help.sap.com/saphelp_snc700_ehp04/helpdata/en/48/d127e1e1c60783e10000000a42189d/content.htm?no_cache=true

#### OR-028 자동 force unlock/인수/Revert/Delete를 복구 정책으로 사용하지 않는다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 자동 force unlock/인수/Revert/Delete를 복구 정책으로 사용하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-028","acceptance":"timeout/cancel/partialfailure fixture에서 해당 operation dispatch가 0인지 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - https://help.sap.com/saphelp_snc700_ehp04/helpdata/en/48/d127e1e1c60783e10000000a42189d/content.htm?no_cache=true
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-029 전송 후 timeout은 UNKNOWN_REMOTE_OUTCOME으로 기록하고 먼저 reconcile한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 전송 후 timeout은 UNKNOWN_REMOTE_OUTCOME으로 기록하고 먼저 reconcile한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-029","acceptance":"서버 처리 후 응답분실 mock에서 두 번째 Create 대신 Read/상태조회로 전환하는지 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-030 부분 성공한 객체/CL/version을 유지하고 의존 후속만 보류한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 부분 성공한 객체/CL/version을 유지하고 의존 후속만 보류한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-030","acceptance":"8객체 중 MM save 실패 fixture에서 성공객체 journal 유지·OM/Directory dispatch 0을 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - https://help.sap.com/docs/SAP_NETWEAVER_731/d0a0a7cb51dc40529bfcac724dd05796/48d24b4142262b63e10000000a42189d.html
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-031 ESR 완료 후 Directory 실패를 전체 rollback으로 표시하지 않는다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: ESR 완료 후 Directory 실패를 전체 rollback으로 표시하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-031","acceptance":"Directory 오류 fixture의 결과가 ESR active 목록과 미완료 Directory를 함께 반환하는지 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-032 Directory severity4 rollback을 단일 call transaction 범위로 한정한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: Directory severity4 rollback을 단일 call transaction 범위로 한정한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-032","acceptance":"2회 성공 후 3번째 call severity4 fixture에서 앞선 성공을 rolled_back으로 덮어쓰지 않는다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - https://help.sap.com/docs/SAP_NETWEAVER_731/d0a0a7cb51dc40529bfcac724dd05796/48d24b4142262b63e10000000a42189d.html

#### OR-033 일괄 create의 item-level commit/rollback 의미를 별도로 검증한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: 일괄 create의 item-level commit/rollback 의미를 별도로 검증한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-033","acceptance":"향후 sandbox에서 정상/오류 혼합 2객체 요청 후 CL membership와 User/Active readback을 대조한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - https://help.sap.com/docs/SAP_NETWEAVER_731/d0a0a7cb51dc40529bfcac724dd05796/48d24b4142262b63e10000000a42189d.html

#### OR-034 GET transport와 SOAP operation별 재시도 정책을 구분한다

- 원본 상태: `IMPLEMENTATION_GAP`.
- 주장·요구 범위: GET transport와 SOAP operation별 재시도 정책을 구분한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-034","acceptance":"Query/Read retry만 bounded 허용하고 Create/Change/Activate POST의 generic retry가 없는지 transport spy로 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/integrations/sap_po/client.py
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-035 credential 오류/계정잠김/password-change-required를 무한 재로그인하지 않는다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: credential 오류/계정잠김/password-change-required를 무한 재로그인하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-035","acceptance":"401/권한오류/password-change-required/일시connection 오류의 재시도 수와 상태를 fake login으로 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-036 로컬 Idempotency-Key와 request digest 충돌 정책을 durable하게 구현한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 로컬 Idempotency-Key와 request digest 충돌 정책을 durable하게 구현한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-036","acceptance":"동일 key+내용은 기존 job 반환, 다른내용409, concurrent insert 시 unique 제약을 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-037 dispatch 전 journal과 응답후 checkpoint 사이 crash는 reconciliation으로 복구한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: dispatch 전 journal과 응답후 checkpoint 사이 crash는 reconciliation으로 복구한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-037","acceptance":"각 commit 경계 crash injection 후 중복 mutation 없이 UNKNOWN 단계에서 재조회하는지 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-038 SID/repository/context/key별 lease와 fencing/CAS를 사용한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: SID/repository/context/key별 lease와 fencing/CAS를 사용한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-038","acceptance":"두 worker/두 plan/expired lease/stale fencing token을 주입하여 중복 진행을 차단한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-039 계획 revision과 contract/SDK/base version fingerprint를 고정한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 계획 revision과 contract/SDK/base version fingerprint를 고정한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-039","acceptance":"SDK/WSDL/normalizer/base snapshot 각각 한 개 변경 시 plan revision 재검사 없이는 실행 불가를 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-040 Directory 로그의 모든 LogMessage*와 중첩 item을 타입별 수집한다

- 원본 상태: `IMPLEMENTATION_GAP`.
- 주장·요구 범위: Directory 로그의 모든 LogMessage*와 중첩 item을 타입별 수집한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-040","acceptance":"global+channel+ICO+CL 메시지 혼합/누락ID/단건배열/빈collection fixture의 모든 item을 손실 없이 파싱한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - PROJECT_ROOT/backend/app/integrations/sap_po/normalize.py

#### OR-041 Severity 1/2/3/4를 정보/경고/오류/종료로 판정한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: Severity 1/2/3/4를 정보/경고/오류/종료로 판정한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-041","acceptance":"severity2 생성불완전,3객체실패,4callrollback,missing/unknown code 결과를 별도 표시한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - https://help.sap.com/docs/SAP_NETWEAVER_731/d0a0a7cb51dc40529bfcac724dd05796/48d24b4142262b63e10000000a42189d.html

#### OR-042 User read와 Active read를 명시하고 각각 draft/active 판정에 사용한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: User read와 Active read를 명시하고 각각 draft/active 판정에 사용한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-042","acceptance":"동일 key의 User/Active가 다른 fixture에서 activation 검증은 Active 결과만 사용한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - https://help.sap.com/docs/SAP_NETWEAVER_750/d0a0a7cb51dc40529bfcac724dd05796/48d2695b0d7d035be10000000a42189b.html
  - PROJECT_ROOT/backend/app/domains/channels/service.py

#### OR-043 activation 응답+active 내용+CL 상태를 함께 확인한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: activation 응답+active 내용+CL 상태를 함께 확인한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-043","acceptance":"향후 sandbox의 Activate 경고/응답분실/성공을 Active readback과 CL 상태로 구분한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d2613e0d7d035be10000000a42189b/content.htm?no_cache=true

#### OR-044 CacheState는 consumer별 notification/refresh/object 상태를 판정한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: CacheState는 consumer별 notification/refresh/object 상태를 판정한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-044","acceptance":"empty/missing consumer/New/In Process/Warning/Failed/Unknown/부분객체성공 fixture를 각각 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d2613e0d7d035be10000000a42189b/content.htm?no_cache=true

#### OR-045 cache 지연은 polling만 하고 full refresh/re-activate를 자동 수행하지 않는다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: cache 지연은 polling만 하고 full refresh/re-activate를 자동 수행하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-045","acceptance":"cache timeout fixture가 CACHE_DELAYED에서 멈추고 재활성화/refresh/채널control dispatch0을 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-046 runtime OK와 메시지 변환·전달 end-to-end 성공을 구분한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: runtime OK와 메시지 변환·전달 end-to-end 성공을 구분한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-046","acceptance":"status-only 검증 결과에는 delivery_verified=false가 유지되고 테스트 메시지 전송이 없는지 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-047 Read의 blank secret을 unknown으로 표시하고 Create/clone에는 secretRef를 요구한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: Read의 blank secret을 unknown으로 표시하고 Create/clone에는 secretRef를 요구한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-047","acceptance":"blank Read password와 explicit new secret/empty secret의 상태를 구분하고 clone readiness를 차단한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d24bcf42262b63e10000000a42189d/content.htm?no_cache=true
  - PROJECT_ROOT/backend/app/domains/channels/bulk_service.py
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-048 표준 Change의 blank password 승계와 삭제 의미를 혼동하지 않는다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: 표준 Change의 blank password 승계와 삭제 의미를 혼동하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-048","acceptance":"향후 sandbox의 지원 어댑터별 omitted/empty/value semantics와 새 Create 결과를 실제 확인한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 근거:
  - https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d24bcf42262b63e10000000a42189d/content.htm?no_cache=true
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json

#### OR-049 자격값은 backend secretRef로 받고 plaintext SOAP 요구는 TLS 조건을 별도 확인한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 자격값은 backend secretRef로 받고 plaintext SOAP 요구는 TLS 조건을 별도 확인한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-049","acceptance":"가짜 secret provider와 TLS policy/secret generation을 검증하고 URL·credential이 frontend DTO에 없는지 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - https://help.sap.com/saphelp_scm700_ehp02/helpdata/en/48/d24bcf42262b63e10000000a42189d/content.htm?no_cache=true
  - PROJECT_ROOT/backend/app/core/security.py
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-050 로그/예외/감사/diff에서 token·cookie·password·rawpayload를 제거한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 로그/예외/감사/diff에서 token·cookie·password·rawpayload를 제거한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-050","acceptance":"고정 fake canary를 모든 header/XML/P4/exception/message 위치에 주입해 출력 artifact에 부재를 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/integrations/sap_po/client.py
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-051 authoring domain과 Directory SOAP adapter/Java worker를 기존 router-service-repository 경계로 분리한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: authoring domain과 Directory SOAP adapter/Java worker를 기존 router-service-repository 경계로 분리한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-051","acceptance":"순수 dependency/unit fixture로 router가 SAP SDK/JAR/credential을 frontend로 전달하지 않는지 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/integrations/sap_po/client.py
  - PROJECT_ROOT/backend/app/core/config.py
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-052 기존 채널 detail의 PartyID 빈값·User context·attrs flatten을 생성 기반으로 재사용하지 않는다

- 원본 상태: `IMPLEMENTATION_GAP`.
- 주장·요구 범위: 기존 채널 detail의 PartyID 빈값·User context·attrs flatten을 생성 기반으로 재사용하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-052","acceptance":"nonempty-party/같은Name다른Namespace/active-vs-user fixture가 원본 typed DTO에 보존되는지 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/domains/channels/service.py
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json

#### OR-053 기존 bulk Excel은 export/preview이고 신규 생성 API가 아님을 분리한다

- 원본 상태: `CONTRACT_CONFIRMED`.
- 주장·요구 범위: 기존 bulk Excel은 export/preview이고 신규 생성 API가 아님을 분리한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-053","acceptance":"기존 bulk route 회귀와 신규 plan request 사이 schema/permission을 분리한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/domains/channels/bulk_service.py

#### OR-054 authoring service names/capability/permissions와 SID 범위를 새로 명시한다

- 원본 상태: `IMPLEMENTATION_GAP`.
- 주장·요구 범위: authoring service names/capability/permissions와 SID 범위를 새로 명시한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-054","acceptance":"Viewer/Operator/Admin 및 허용SID/차단SID 조합에서 계획/실행/활성화 권한을 backend에서 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/core/security.py
  - PROJECT_ROOT/backend/app/core/config.py
  - PROJECT_ROOT/backend/app/integrations/sap_po/client.py

#### OR-055 cached Zeep client/session의 thread scope·credential refresh·WSDL invalidation을 검증한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: cached Zeep client/session의 thread scope·credential refresh·WSDL invalidation을 검증한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-055","acceptance":"동시 job fixture 및 credential/contract 변경에 cached session이 잘못 재사용되지 않음을 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/integrations/sap_po/client.py

#### OR-056 Query wrapper/배열을 key overlap heuristic 대신 exact contract로 파싱한다

- 원본 상태: `IMPLEMENTATION_GAP`.
- 주장·요구 범위: Query wrapper/배열을 key overlap heuristic 대신 exact contract로 파싱한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-056","acceptance":"CommunicationChannelQueryOut.CommunicationChannelID[] fixture에서 전건·단건·0건 count와 party를 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/integrations/sap_po/normalize.py
  - PROJECT_ROOT/backend/app/domains/channels/service.py

#### OR-057 channel 생성/활성화의 polling·업무 트래픽 유발 시점을 adapter별로 확인한다

- 원본 상태: `EXECUTION_UNVERIFIED`.
- 주장·요구 범위: channel 생성/활성화의 polling·업무 트래픽 유발 시점을 adapter별로 확인한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-057","acceptance":"허용된 독립 sandbox의 대상 시스템 연결이 격리된 채널에서 create/save/activate 각 단계의 runtime 동작을 관찰한다","scope":"future_sandbox_write","may_run_in_current_request":false,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-058 MM 테스트/UDF/lookup 실행을 단순 read로 취급하지 않는다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: MM 테스트/UDF/lookup 실행을 단순 read로 취급하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-058","acceptance":"로컬 순수함수 1:1 fixture와 외부 lookup test capability를 분리하고 현재 runtime test dispatch0을 검사한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/mm-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-059 취소는 미전송 단계 중단이며 원격취소/rollback 보장이 아니다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 취소는 미전송 단계 중단이며 원격취소/rollback 보장이 아니다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-059","acceptance":"in-flight request 중 취소와 응답후 취소의 결과가 남은draft/active 객체를 정확히 기록하는지 확인한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-060 durable plan/execution/step/ref/lease/audit 저장은 기존 PostgreSQL migration으로 추가한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: durable plan/execution/step/ref/lease/audit 저장은 기존 PostgreSQL migration으로 추가한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-060","acceptance":"새 migration의 unique/FK/CAS/lease/retention과 crash recovery를 별도 테스트DB에서 검증한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-061 new operation/UI/contract/SDK upgrade는 도메인 문서·fixture·회귀를 함께 갱신한다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: new operation/UI/contract/SDK upgrade는 도메인 문서·fixture·회귀를 함께 갱신한다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-061","acceptance":"pin된 fixture와 type change 탐지, 기존 read/control API 회귀 및 no-write 검증을 포함한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - PROJECT_ROOT/backend/app/core/config.py
  - PROJECT_ROOT/backend/app/integrations/sap_po/client.py
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

#### OR-062 정적 계약·오프라인 XSD 통과를 실제 생성권한·저장·활성화 성공으로 표시하지 않는다

- 원본 상태: `DESIGN_SPECIFIED`.
- 주장·요구 범위: 정적 계약·오프라인 XSD 통과를 실제 생성권한·저장·활성화 성공으로 표시하지 않는다
- `sap_live_verified`: `false`.
- 남은 구현·시험: {"id":"OT-062","acceptance":"모든 API progress/result에 evidence_scope와 live_verified=false 필드를 포함하고 준비도 성공률 계산을 금지한다","scope":"offline","may_run_in_current_request":true,"executed":false}
- 근거:
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-contracts.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/directory-offline-validation.json
  - RESEARCH_ROOT/pimon-analysis-20261018/esr-external-authoring/transport-evidence.json
  - RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/orchestration-findings.md

## REF 2 Repository SDK 45개 파일의 당시 pin

다음 목록은 과거 JNLP가 선언한 순서와 SHA-256이다. 라이브러리 자체를 공개 배포하지 않는다. 본사 설치가 다른 SP/patch이면 이 SHA와 다를 수 있으므로 과거 JAR를 강제로 섞지 말고 새 fingerprint와 검증 결과를 만든다. 45개 전체 사용은 최소 classpath 증명이 아니다.

원본은 `RESEARCH_ROOT/pimon-analysis-20261019/implementation-readiness/classpath-inventory.json`이다. CRC와 존재한 서명 멤버를 확인했지만 cryptographic signature trust validation을 수행한 것은 아니다. 중복 클래스는 21개이고 한 클래스의 bytes가 달랐다. 관측한 Java 8 초과 major 53은 JAXB XJC의 `module-info.class` 하나였으며 전체 SDK가 Java 9를 요구한다는 뜻은 아니다.

| JNLP 순서 0부터 | JAR | bytes | SHA-256 |
|---:|---|---:|---|
| 0 | `com.sap.xpi.ibrep.client.jar` | 6611115 | `bdad0c47357e6e72db6fae6241f10a43fefb4e555402b35e1c18d94df513c812` |
| 1 | `com.sap.xpi.ibrep.core.jar` | 998473 | `7ba3147ffbca2e4ddb9cb903c032e0fc794dd3cad5cbfd18fed7c973b56a1d8b` |
| 2 | `com.sap.xpi.ibrep.rb.jar` | 1690902 | `6d2b2bcb813bd381b92f3bf5f8d68564dd53220fd08a1643ff627c0cf527d5fc` |
| 3 | `com.sap.xpi.ib.client.jar` | 5321722 | `e5cdf8595b9b830a4ec87eceff6985f94d3675caf23db86d36486be2caf35eae` |
| 4 | `com.sap.xpi.ib.core.jar` | 3470652 | `7963edad9c03f7c0f80455677e540f2b020c5895b8fe759d935f9af77c82aa43` |
| 5 | `com.sap.xpi.ib.rb.jar` | 2287614 | `675592ed442d1259af264a8b38640f200fb5b7dad75b259728af12060eb7e727` |
| 6 | `com.sap.xpi.ib.mt.gui.lib.jar` | 1426543 | `8661d373f24e156af39dae28bd5308f975d8c5115f3422c14015edf5a2a1fbd0` |
| 7 | `com.sap.xpi.ib.mt.rb.jar` | 294924 | `59aad50e9eeff54dbe0d97f0693648d15b99e639fd4e4f4fc39ca9e71e203694` |
| 8 | `com.sap.xpi.ib.mt.util.lib.jar` | 47323 | `1d3543038017b3cacb5a4dcd4700414432654c73a169c5d454e77cacd9f046b0` |
| 9 | `com.sap.xpi.ib.mapping.lib.jar` | 88227 | `2dd1cfe0d30717852514fb324c0dc68267e0c4f9e0e078c2f70b475833c2dac1` |
| 10 | `com.sap.xpi.ib.upload.core.jar` | 63167 | `d9db2ee3a320d70e4e4b87f406dec5ce8c67fadc97ccb96d03d4cc00f341dc04` |
| 11 | `com.sap.xpi.ib.upload.sap.jar` | 163982 | `b2d9aa6b1203dff7570c8b897266a8ea77a053b94e24a89d4e242e27198469b0` |
| 12 | `com.sap.xi.mapping.tool.lib_api.jar` | 506128 | `cc49624f22a31f0ffeefeaec4aca314f263f03757078b8f596c015f24a1f59c5` |
| 13 | `com.sap.xi.flib.lib_api.jar` | 67411 | `3a531c389d3fcee96869a3af54a284e11310ed8e43da6d2a955cc1f360f8c717` |
| 14 | `com.sap.aii.utilxi.core.jar` | 1953145 | `306ac9a0e13e6a363779b2b39ff6c0ea8865a31fe4d4ae3c06ea4058410dafbd` |
| 15 | `com.sap.aii.utilxi.gui.jar` | 3862625 | `6dec45b570c715e0ca0b79f5f53b42174eafb808850e8463ac929a722789a2b6` |
| 16 | `com.sap.xpi.util.rb.jar` | 326061 | `bea88ad71759f813c8ac06f961228522e72833b17baa7c6114bb1eef807794e1` |
| 17 | `com.sap.aii.proxy.gen.jar` | 295827 | `0efa3e124138e3c746c926165420ecd01b64d16a9cbd9e9c1b87cc49f0555e36` |
| 18 | `frog.jar` | 680847 | `4a4a239cb456ee080c4b30e9628816a7a4b5671a84020ad295eaa8d7311573a5` |
| 19 | `com.sap.xpi.ibrep.core.subn.jar` | 58597 | `debdbf484d8e93ab3c8b27ab513c49df867844084c318117e3b12ec4dfa99a09` |
| 20 | `jta.jar` | 19798 | `fb2e9f2c0949b393b70ccbaeab87d963736fefc8752c3cd4dd9b89d64e471eff` |
| 21 | `ejb20.jar` | 25567 | `8da61d90aa03b78b212afab40f82d53b8c5441876cdf81e49f974e06642a2cd4` |
| 22 | `sap.com~tc~sapxmltoolkit~sapxmltoolkit.jar` | 1690253 | `a2d08ff0e111cae1a0b70d8be565d3c09082ac1dd86e26a9b3ca27fb6915a90b` |
| 23 | `sap.com~tc~exception~impl.jar` | 74340 | `076f4a4adc2e1ad74ca264ba1cae172451883c44b92dc377dafb158f45ec0360` |
| 24 | `sap.com~tc~logging~java~impl.jar` | 346845 | `1810d41bea124374f1b19cd09314b10a8c7c7e7dceca70382beee4304e059848` |
| 25 | `sap.com~tc~bl~guidgenerator~impl.jar` | 23708 | `93d5e4990dff0cb37b4dc220ba8bc594a0d40bd9faf4892465c12723e1c8188e` |
| 26 | `jperflib.jar` | 22781 | `fb0d67775f348813b72d3815fd2a1f1271d76894d5fe070e0898bc77cce848ce` |
| 27 | `sap.com~tc~bl~ni~impl.jar` | 27526 | `28cd8ddb07336ef30b7c8ab1e18c6be8ffe404b03a992cabdd55fbfb1b9ba49e` |
| 28 | `sap.com~tc~je~clientlib~impl.jar` | 15681478 | `1f4ce41f3416ec8be66b25e14f73cd38b5134eb3229082dec9e6187eebda2542` |
| 29 | `sap.com~tc~bl~jarm~jarm.jar` | 111793 | `fd7fa70399253f59e8c21fee3507779095a1447bf24e2d4cbb1890e9df6cc12a` |
| 30 | `tenComposite.jar` | 616555 | `f040503b98fda38dbbee8719b3356f0947827138ed08a4e22744e88051238f95` |
| 31 | `tenGraph.jar` | 1134272 | `34587225fcf78cd4ed7ab23390fbe6c91481b31c0446ebab6d3dba81f0fdb9e5` |
| 32 | `tenGraphics.jar` | 301384 | `04e195017c44c884c248ed08ca1c72c205ef64f637d5dd44d2d13dc043bb4805` |
| 33 | `tenGenerics.jar` | 292274 | `e671872a5e60cae326f6d8c4325fd6f2df420567cd6ed686f09f1e598769f22f` |
| 34 | `tenGui.jar` | 1692684 | `708884bf28ad43b18bd2056b54518d2fe976aa2cf2c030f33c7e147d9e928959` |
| 35 | `tenGuiResource.jar` | 361664 | `d963d3e4ff8976038f575cf314b34b935e863137b70a4017c6067fbef07be276` |
| 36 | `com.sap.xpi.ibrep.maestro.core.jar` | 1151675 | `a75b93161c3880bf6787f0a5e4a0f5e4926c9fac7f346f0e63872b7bbaf05bcd` |
| 37 | `com.sap.xpi.ibrep.maestro.model.jar` | 370694 | `320e26cd79f4e313ecf35e9d72c3b35aaa840fa30c0ed438e23fe36e6c3119a9` |
| 38 | `tenSkeleton.jar` | 384356 | `4b2bce42d41e4b8896897e66307ccc0a90574eb7cfcc846dce58e4d443daa4fa` |
| 39 | `tenLookAndFeel.jar` | 248806 | `9829de0cf5379a0b177c20f20e626ca9f67a328a147e48aeddb9b5db5245e047` |
| 40 | `com.sun.xml.bind-jaxb-xjc-3.0.2.jar` | 2020375 | `81f5edbad188236d1c10eda3b79dcca60d1456e75803d9abc92c725980643586` |
| 41 | `iaik_jsse.jar` | 38609 | `0e836abb683762048f3b3c8cd6f21f83ef9425208ae80396a26e64c62106a99d` |
| 42 | `iaik_smime.jar` | 42710 | `bd29ff5c49a4011ac8384593324c8eef3d330daa0be616c6369e2a3582162540` |
| 43 | `iaik_ssl.jar` | 383664 | `5add7bf842687aa051759ea8b776eed0e3c01431b8478bf7fe273cef04960c7d` |
| 44 | `w3c_http.jar` | 249502 | `6aad66bac89786db8b5325f0edde9854d9ebed5735b9ffe913586b61d2c75fc9` |

## REF 3 KBA 3549157에서 확보한 테이블명 174개

다음은 이름 catalog일 뿐 설치 DB schema·SQL 계약이 아니다. 고유 이름 174개가 모두 `XI_DIR*`이고 원문 이름 출현 178회 중 4개가 중복이었다. 임의의 column/join/실행 상태 의미를 유추하지 않는다. 현재 DB가 준비되지 않아 실제 설치 존재도 검증하지 않았다. 원문 전체 설명을 복제하지 않고 사실적 식별 이름만 나열한다.

```text
XI_DIRTSRP_ENTITY
XI_DIRDATASERVICE
XI_DIRKEYNAME
XI_DIRCACHEEVENT
XI_DIRCACHEOBJ
XI_DIRDATAPERSON
XI_DIRDATASRVIDS
XI_DIR_TXTOGR_VERS
XI_DIRDATAPARTYIDS
XI_DIR_TXTSHT_VERS
XI_DIR_TXTOBJ_VERS
XI_DIRDATA_LNK
XI_DIRDATACHANNEL
XI_DIRSYNCADMIN
XI_DIRCHANGELIST
XI_DIRKEYSERVICE
XI_DIRSYNC_RD_RULE
XI_DIR_TXTSHT_SYNC
XI_DIRKEY_RD_RULE
XI_DIRDATAADMIN
XI_DIRSYNCCHANNEL
XI_DIRKEYPARTY
XI_DIRSYNCPARTYIDS
XI_DIRKEY_DIR_VIEW
XI_DIRSYNCDIRVIEWN
XI_DIRSYNC_LNK
XI_DIRSYNCMODULESQ
XI_DIRSYNCMODULECF
XI_DIRSYNC_RD_EXTR
XI_DIRSYNCSERVICE
XI_DIRSYNCSRVIDS
XI_DIRKEYCHANNEL
XI_DIRBND
XI_DIRCACHEERRORS
XI_DIRCACHERCLVIEW
XI_DIRDATAALLINONE
XI_DIRDATAALRU_CON
XI_DIRDATAALRU_ERR
XI_DIRDATAALRU_RT
XI_DIRDATABHDMPNG
XI_DIRDATABINDIF
XI_DIRDATABLOB
XI_DIRDATABPCONT
XI_DIRDATABPPROP
XI_DIRDATADIRVIEWN
XI_DIRDATAFOLDER
XI_DIRDATAHEAD_RU
XI_DIRDATAIFL
XI_DIRDATAIFLBLB
XI_DIRDATALINK
XI_DIRDATAMAPDRELA
XI_DIRDATAMAPDRELG
XI_DIRDATAMAPDRELS
XI_DIRDATAMODULECF
XI_DIRDATAORIGINAL
XI_DIRDATAPIPCONF
XI_DIRDATAPIPCOPAR
XI_DIRDATAUSERIDS
XI_DIRDATAVALMAP
XI_DIRDATAVALMAPGR
XI_DIRDATAVALMAPN
XI_DIRDATAVALUEMAP
XI_DIRDATA_AIOPROP
XI_DIRDATA_CONN
XI_DIRDATA_CSTATE
XI_DIRDATA_RD_COND
XI_DIRDATA_RD_DYN
XI_DIRDATA_RD_EXTR
XI_DIRDATA_RD_NSP
XI_DIRDATA_RD_REL
XI_DIRDATA_RD_RULE
XI_DIRDATA_SCEN
XI_DIRDATA_SMAP
XI_DIRIFLDPL
XI_DIRIFLDPLLG
XI_DIRKEYADAPTERMD
XI_DIRKEYALERTRULE
XI_DIRKEYARCHVSUB
XI_DIRKEYBINDING
XI_DIRKEYBINDP2P
XI_DIRKEYEXTPROG
XI_DIRKEYFOLDER
XI_DIRKEYIFL
XI_DIRKEYMAPKIDET
XI_DIRKEYPC
XI_DIRKEYPIPCONF
XI_DIRKEYSUBNAME
XI_DIRKEYVALMAP
XI_DIRKEYVALMAPCTX
XI_DIRKEYVALMAPGRP
XI_DIRKEYVALMAPSCH
XI_DIRKEYVALMAPTYP
XI_DIRKEYVALUEMAP
XI_DIRKEY_ALLINONE
XI_DIRKEY_RD_RELAT
XI_DIRKEY_SCENARIO
XI_DIROPENCONFLICT
XI_DIRSM_CONFIG
XI_DIRSM_LINKS
XI_DIRSM_SCENARIO
XI_DIRSM_TEXT
XI_DIRSNAPSHOTS
XI_DIRSYNCALLINONE
XI_DIRSYNCALRU_CON
XI_DIRSYNCALRU_ERR
XI_DIRSYNCALRU_RT
XI_DIRSYNCBHDMPNG
XI_DIRSYNCBINDIF
XI_DIRSYNCBLOB
XI_DIRSYNCBPCONT
XI_DIRSYNCBPPROP
XI_DIRSYNCFOLDER
XI_DIRSYNCHEAD_RU
XI_DIRSYNCIFL
XI_DIRSYNCIFLBLB
XI_DIRSYNCLINK
XI_DIRSYNCMAPDRELA
XI_DIRSYNCMAPDRELG
XI_DIRSYNCMAPDRELS
XI_DIRSYNCPIPCONF
XI_DIRSYNCPIPCOPAR
XI_DIRSYNCTXT_L
XI_DIRSYNCTXT_S
XI_DIRSYNCUSERIDS
XI_DIRSYNCVALMAPGR
XI_DIRSYNCVALMAPN
XI_DIRSYNC_AIOPROP
XI_DIRSYNC_CONN
XI_DIRSYNC_RD_COND
XI_DIRSYNC_RD_DYN
XI_DIRSYNC_RD_NSP
XI_DIRSYNC_RD_REL
XI_DIRSYNC_SCEN
XI_DIRSYNC_SMAP
XI_DIRTEXTHEAD
XI_DIRTEXTLONG
XI_DIRTEXTLONG_TX
XI_DIRTEXTSHORT
XI_DIRTEXTSHORT_TX
XI_DIRTPCOLLECTION
XI_DIRTPINFO
XI_DIRTPPERFORM
XI_DIRTPPROTOCOL
XI_DIRUPGRADEDATA
XI_DIRVERSION
XI_DIRWORKSP
XI_DIRWORKSPACE
XI_DIRWORKSP_DEP
XI_DIR_API_CHANNEL
XI_DIR_API_CT
XI_DIR_API_TUCC_CL
XI_DIR_P2P_API_CT
XI_DIR_P2P_CHANNEL
XI_DIR_P2P_TUCC_CL
XI_DIR_TXTLNG_SYNC
XI_DIR_TXTLNG_VERS
XI_DIRDATAALRULE
XI_DIRDATAALRU_OBJ
XI_DIRDATABINDING
XI_DIRSYNCALRULE
XI_DIRSYNCALRU_OBJ
XI_DIRLINK
XI_DIRKEYLINK
XI_DIRAPIREV
XI_DIRCACHE
XI_DIRCHDL
XI_DIRDELTA
XI_DIRKEY
XI_DIRLINKC
XI_DIRMSGEXC
XI_DIRMSGLOG
XI_DIRPRELOAD
XI_DIRRULE
XI_DIRRULELOG
```

## REF 4 핵심 원본 파일과 SHA-256

이 목록은 내부 반입 자료를 대조하기 위한 정보다. GitHub Markdown에 해당 원본이 첨부됐다는 뜻이 아니다. 원본의 SHA는 경로를 재바인딩하기 전 파일 기준이며, 작업 사본을 수정했다면 별도 SHA와 변환 이력을 기록한다.

| RESEARCH_ROOT 상대 경로 | bytes | SHA-256 |
|---|---:|---|
| `output/po-consolidated-document-20261022/SAP_PO_Consolidated_Analysis_20261022.docx` | 182855 | `4b1493a59b5a7d1014d26650e7fe9831042140d5bf64be276da38b560ce60623` |
| `pimon-analysis-20261015/nwa-readonly/metrics-contract.csv` | 8089 | `ad0ab6d14908689fb69c39e1ce4e9e252916f4b108c357ae5f414360b04b8803` |
| `pimon-analysis-20261015/soap-session-44-verification/request.xml` | 13164 | `aa001ec43c79a0682ec5547812c134b18a00cabee6d812c9da23a8e2b96755ff` |
| `pimon-analysis-20261015/soap-session-44-verification/verification.json` | 2497 | `d246ec37ee523d5caf1e71509e600bde3f7997835adab619f351356b8d3cb39a` |
| `pimon-analysis-20261015/collector-session-verification/findings.md` | 8330 | `d603eb06a141f16fd9720aaa77f28abf0a17c3708e559321bc8328ffc65866b7` |
| `pimon-analysis-20261015/collector-session-verification/verification.json` | 5894 | `a1c456d0009e06691cd17ddf6ef3ce0273126102255d8d6f5bac9ba006033cf7` |
| `pimon-analysis-20261018/standard-message-soap/findings.md` | 8179 | `3b58d86c2638a8a49c49b817de9d99bcf33fac05e64c5f0033c7c1189d83215c` |
| `pimon-analysis-20261018/standard-message-soap/qa-contract.json` | 3386 | `46dc153244ecde7165d2f18b71bc56e72ba4b62441ede9c5131ac7002a5a2122` |
| `pimon-analysis-20261018/standard-message-soap/verification.json` | 2177 | `463e8ece610419bb049d87a95bc3115e8feb4741646a190536161b24880186ba` |
| `pimon-analysis-20261018/standard-channel-status/findings.md` | 7183 | `f156630d907f6f996ce1a2ee01c668d2eea9ee6297e18c3ef9e887e6ec9866e0` |
| `pimon-analysis-20261018/standard-channel-status/ChannelAdmin.xsd` | 8507 | `aef91f5ebd748c7c5c3f6ce24fda0a1a29f6f63476201bb735c714f3591813fa` |
| `pimon-analysis-20261018/standard-channel-status/verification.json` | 5203 | `5c758c484721d032342c1cf515789272be0782de01d248bbedf76bc3891f42f4` |
| `pimon-analysis-20261019/implementation-readiness/implementation-spec.md` | 23866 | `06b2e691918ab117c5c652a41f9cf4ac6ef5bd7565b875469463bfcc473c409f` |
| `pimon-analysis-20261019/implementation-readiness/bootstrap-findings.md` | 17184 | `4a1057bb66626a202a3504f2b5acd6ff828b558db277e160c32de38b28441653` |
| `pimon-analysis-20261019/implementation-readiness/models-findings.md` | 25425 | `7b4e9bf1c178d5ed3f3858f47b5f2c4c37304330388bb08501cd5a0671c3064d` |
| `pimon-analysis-20261019/implementation-readiness/orchestration-findings.md` | 31413 | `59c97f58d82e35f756f4ffbcdc052ad672428596433d76a93dab25826009bde5` |
| `pimon-analysis-20261019/implementation-readiness/directory-contracts.json` | 349119 | `112895cccfe05f16d1266bdf36714120cb22aa8ef5c056e0c7092e1766d1a1f2` |
| `pimon-analysis-20261019/implementation-readiness/directory-offline-validation.json` | 4680 | `e68279d6ed2b76e51c81304580c92ac1d1472e633c2944bb445d0c80f9c5016d` |
| `pimon-analysis-20261019/implementation-readiness/classpath-inventory.json` | 43737 | `e9e4e63605ad71d285316bac6f8c86f8df9b102bbb8c32d01c101f19080d2a6b` |
| `pimon-analysis-20261019/implementation-readiness/readiness-ledger.json` | 150714 | `5bbea8f3c73a4ba637703ac9250b6665dcc9777efb17cb5be4ba709004712afd` |
| `pimon-analysis-20261019/implementation-readiness/qa-findings.md` | 5400 | `39319897acf9aa30f198a8120c36ee91c3a38dc0ca862b935160c050f0c590b0` |
| `pimon-analysis-20261019/implementation-readiness/qa-results.json` | 25047 | `bd1a4b0680c441945fd3dc0a9bfdf246072d289edf6a39d4b8294834bc4f6518` |

## REF 5 본사 에이전트 완료 보고 형식

각 구현 묶음은 아래 정보를 내부 결과 문서에 남긴다. 공개 GitHub에는 비밀값·원본 계약·업무 식별값을 넣지 않는다.

```json
{
  "task_ids": [
    "P0-example"
  ],
  "base_commit": "actual-head-sha",
  "changed_files": [],
  "tests_executed": [],
  "tests_not_executed": [],
  "external_calls": {
    "sap_read": 0,
    "sap_mutation": 0,
    "db_read": 0
  },
  "evidence_scope": "offline",
  "live_verified": false,
  "contract_fingerprints": [],
  "remaining_unknowns": [],
  "rollback": "application-code-and-own-schema-plan-only"
}
```

샘플 숫자·합성 XML·mock 결과를 실제 운영 결과로 보고하지 않는다. 생성·활성화·cache 반영·메시지 전달은 각각 별도 완료 조건이다. 이 인계서의 공개 날짜가 과거 SAP 관측값의 최신성을 보장하지 않는다.
