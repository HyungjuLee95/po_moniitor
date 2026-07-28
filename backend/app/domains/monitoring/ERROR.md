# Monitoring ERROR
수치 불일치는 timezone, message 중복, 상태 집계식, collector checkpoint 순으로 확인한다.

## 2026-07-28 / 평균 응답 표시 범위와 실제 집계 범위 불일치
- 증상: 화면은 최근 15분으로 표시했지만 API는 24시간 집계를 반환했다.
- 영향: 현재 지연 상황을 과거 평균으로 오판할 수 있었다.
- 원인: RTIMS 집계 범위가 UI 문구와 분리되어 있었다.
- 해결: `MON_MSG_LOG` elapsed 합계를 설정된 분 단위 window로 계산하고 지연 목록과 같은 policy를 사용했다.
- 검증: monitoring service contract test와 frontend build를 통과했다.
- 재발 방지: window와 threshold를 API meta와 화면에 함께 표시한다.
