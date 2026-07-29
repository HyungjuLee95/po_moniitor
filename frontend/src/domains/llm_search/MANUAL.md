# LLM Search MANUAL
프론트는 `/llm-search/analyze`에 JSON을 보내고 provider 주소는 알지 못한다. 실제 provider 호출과 context allowlist는 backend 책임이다. 연결 실패 시 실행 결과로 오인하지 않는 안내를 표시하고 원문 payload를 전송하지 않는다.
