# Interfaces MANUAL
표시 이름과 SAP 기술키를 분리하고 동일 이름의 namespace 충돌을 허용하지 않는다.

Namespace 인벤토리는 InterfaceMonitor WSDL operation 목록을 확인한 뒤 지원되는 조회 operation을 호출한다. 사내 SAP 버전의 실제 operation 이름과 응답 wrapper는 smoke test하고 차이가 있으면 ERROR에 기록한다.
