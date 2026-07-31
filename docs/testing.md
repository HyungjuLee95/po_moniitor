# 테스트 전략

## 목적

요구사항 충족, 도메인 API 호환성, 권한 경계, 외부 시스템 실패와 기존 기능 회귀를 위험에 비례해 검증한다.

## 테스트 계층

| 계층 | 대상 | 실행 시점 |
|---|---|---|
| 문서 검사 | 필수 문서·도메인 색인·로컬 링크·민감 파일 | 모든 변경 |
| 정적 검사 | TypeScript·ESLint·Python import | 관련 영역 변경 |
| 단위 | formatter·service·repository 변환·권한 | 도메인 변경 |
| 통합 | FastAPI route·DB·SAP/RTIMS adapter | 계약 또는 경계 변경 |
| 렌더 | Next.js production build와 로그인 HTML | frontend 변경 |
| E2E/스모크 | 로그인·조회·제어·다운로드 핵심 흐름 | 사내 배포 전후 |
| 회귀 | 기존 핵심 기능 | 영향 범위에 따라 |

## 로컬 검증 명령

문서:

```powershell
cd D:\toyproject\PO_MONITOR_MAIN
python scripts\validate_project_docs.py
```

Frontend:

```powershell
cd D:\toyproject\PO_MONITOR_MAIN\frontend
npm run lint
npm test
npm audit --omit=dev
```

Backend:

```powershell
cd D:\toyproject\PO_MONITOR_MAIN
python --version
python -m pytest backend\tests
```

최종 사내 이식 검증의 Python은 반드시 3.11.7이어야 한다. 다른 버전에서 실행한 결과는 보조 검증으로만 기록한다.

## 필수 사례

- 정상 입력과 빈 결과
- 잘못된 입력과 경계값
- 인증 실패·권한 거부·서버 범위 거부
- 외부 시스템 timeout·부분 실패·비활성화
- 중복 요청·재시도·SSE 중단
- 날짜·타임존·00:00~23:59:59 경계
- Excel 파일 형식·필수 열·masking preview
- 사용자별 저장값 복구와 backend unavailable fallback

## 외부 시스템 실검증

실제 SAP PO·RTIMS·HANA·Oracle IFS·LLM 검증은 테스트 계정과 허용된 서버에서 수행한다. 다음을 결과에 남긴다.

1. 환경과 서버 식별자(비밀값 제외)
2. 호출 기능과 입력 조건
3. 실제 확인한 필드·단위·상태 코드
4. 성공·실패 결과
5. 미확인 범위와 운영 위험

## 결과 보고

- 실제 실행한 명령과 통과·실패 수
- 코드상으로만 검토한 범위
- 환경 부족으로 실행하지 못한 항목
- 실패가 발생했다면 관련 `ERROR.md` 갱신 위치
