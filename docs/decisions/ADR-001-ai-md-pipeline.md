# ADR-001 기존 도메인 계약을 보존한 AI MD 파이프라인

## 상태

승인

## 날짜

2026-07-31

## 배경

프로젝트에는 frontend와 backend에 걸쳐 이미 도메인별 `README/MANUAL/SKILL/ERROR/API` 세트가 있다. 새 템플릿은 루트 상태 문서와 자동 검증에 강점이 있지만 `domains/` 단일 루트와 `DOMAIN/ERRORS/SKILLS/TESTS` 파일명을 전제한다. 그대로 복사하면 중복된 기준 문서와 대규모 링크 변경이 발생한다.

## 결정

- 기존 frontend/backend 물리 경계와 도메인별 5개 문서 이름을 유지한다.
- 템플릿의 `DOMAIN.md` 역할은 기존 `README.md`, 공개 계약 역할은 기존 `API.md`가 담당한다.
- 템플릿의 `ERRORS.md`, `SKILLS.md`는 기존 단수형 `ERROR.md`, `SKILL.md`로 통합한다.
- `PROJECT.md`, `CURRENT_TASK.md`, `ROADMAP.md`, `CHANGELOG.md`, 설계·품질 문서는 새로 도입한다.
- 검증 스크립트는 두 도메인 루트와 기존 5개 문서 계약을 검사한다.

## 검토한 대안

1. 템플릿 그대로 전체 이름 변경: 구조는 통일되지만 기존 링크·지침·사용자 요구와 충돌한다.
2. 기존 구조만 유지: 문서가 풍부해도 현재 작업 범위와 자동 품질 게이트가 부족하다.
3. 혼합형 적용: 새 상태·검증 계층을 얻으면서 기존 API 중심 도메인 계약을 보존한다.

## 결과

- 장점: 기존 코드와 링크에 미치는 영향이 작고 AI의 초기 문맥을 줄일 수 있다.
- 비용과 단점: 일반 템플릿과 파일명이 달라 전용 검증 스크립트를 유지해야 한다.
- 후속 작업: 마일스톤마다 문서 색인·링크·코드 계약 일치 여부를 검토한다.

## 관련 문서와 코드

- [`../../AGENTS.md`](../../AGENTS.md)
- [`../../PROJECT.md`](../../PROJECT.md)
- [`../documentation-policy.md`](../documentation-policy.md)
- [`../../scripts/validate_project_docs.py`](../../scripts/validate_project_docs.py)
