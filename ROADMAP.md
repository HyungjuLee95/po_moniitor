# PO_MONITOR_MAIN 로드맵

## 현재 단계

- 단계: `BETA / INTERNAL_VALIDATION`
- 목표: 외부에서 구현한 기능을 사내 SAP PO·RTIMS 환경에서 검증하고 운영 안정성을 확보한다.
- 상세 구현 현황: [`docs/LEGACY_FEATURE_COVERAGE.md`](docs/LEGACY_FEATURE_COVERAGE.md)

## 마일스톤

| ID | 목표 | 상태 | 완료 조건 |
|---|---|---|---|
| M1 | AI 친화 문서 파이프라인 | 완료 | 기준 문서·도메인 색인·자동 문서 검사 적용 |
| M2 | 사내 SAP PO·RTIMS 통합 검증 | 대기 | 핵심 조회·제어·단위·필드 mapping smoke test 통과 |
| M3 | 장애 알림과 LLM 실연동 | 대기 | RTIMS Alert 원본과 내부 JSON LLM API 연결·권한·마스킹 검증 |
| M4 | Collector 운영 강화 | 대기 | 시간창 분할·중복 제거·페이지 수집·분산 잠금 검증 |
| M5 | 운영 보안 강화 | 대기 | 비밀번호 만료·로그인 잠금·대량 작업 감사 기준 확정 |

## 다음 작업

1. 실제 사내 SAP PO에서 채널·Audit·InterfaceMonitor operation과 응답 wrapper 확인
2. RTIMS SQL 필드·시간 단위·Queue·리소스 수치 smoke test
3. HRD HANA 조인과 HttpAdapter sender mapping 확인
4. 실제 Alert Inbox와 내부 LLM JSON API 연동

## 백로그

- RTIMS `LONG_RUNNING` 전용 이력
- Collector 다중 인스턴스 분산 잠금과 scheduler
- 사용자 비밀번호 만료·로그인 잠금 정책
- Legacy 연결 정상·오류 판정 원본 확정

## 보류 원칙

- 사내 원본을 확인할 수 없는 상태 코드와 필드는 추정 구현하지 않는다.
- 비밀값과 운영 데이터는 외부 개발 환경이나 Git에 옮기지 않는다.
- HRD 신규 요구는 기존 필수 이식 범위와 분리해 수용 기준부터 확정한다.
