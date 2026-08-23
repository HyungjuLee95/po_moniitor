# Configuration
`.env`를 검증하고 SID 기반 SAP PO server registry, bootstrap 응답과 서버별 모니터링 policy를 제공한다. 각 서버는 독립적인 origin·credential·SAP endpoint path를 가질 수 있다. 내부 LLM JSON endpoint는 `LLM_API_URL`로 관리하며 공개 설정 응답에는 포함하지 않는다. RTIMS schema-owner 계정은 runtime 계정과 분리하며 원클릭 DDL script에서만 읽는다.
