# Frontend

React 19.2.7 기반 운영 콘솔이다. `app`은 렌더링 진입점, `src/app`은 애플리케이션 조립, `src/core`는 전역 계약, `src/domains`는 업무 기능을 담당한다.

| 도메인 | 책임 |
|---|---|
| auth | 로그인 화면과 세션 |
| dashboard | 위젯 registry, 배치, 개인 설정 |
| server | 서버 선택 표시 계약 |
| monitoring | 운영 요약 시각화 |
| channels | 채널 상태·제어·채널별 통계 |
| messages | 최근 메시지와 Message ID Audit |
| interfaces | 시스템별 채널과 topology |
| incidents | 장애 관리 |
| collectors | 환경 설정 하위 Collector 상태 |
| workspaces | 프로젝트 작업과 단계 진행 |
| settings | 연결·모니터링 기준·사용자 권한·수집 상태 |
| alerts | 상단 점멸 알림과 목록 |
| llm_search | 장애 원인 검색 UI |

작업 전 `MANUAL.md`, `SKILL.md`, 대상 도메인의 네 문서를 읽는다.

## 실행 명령

```powershell
cd D:\toyproject\PO_MONITOR_MAIN\frontend
npm install
npm run dev
```

검증과 운영 빌드:

```powershell
npm run lint
npm test
npm run build
npm run start
```
