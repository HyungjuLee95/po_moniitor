# Interfaces MANUAL
표시 이름과 SAP 기술키를 분리하고 동일 이름의 namespace 충돌을 허용하지 않는다.

Business System 전체 목록은 BusinessSystemIn `Query(BusinessSystemID=None, Description=None, AdministrativeData=None)`로 조회하고 `BusinessSystemID[].ComponentID`를 사용한다.

Namespace 인벤토리는 InterfaceMonitor `getAllInterfaces()`를 우선 호출한다. 현재 실검증 응답의 `fromAction/fromActionNamespace/fromService`를 출발 인터페이스로, `toAction/toActionNamespace/toService`를 도착 operation과 시스템으로 변환한다. 다른 SAP 버전의 일반 `interfaceName/interfaceNamespace` wrapper도 하위 호환한다.
