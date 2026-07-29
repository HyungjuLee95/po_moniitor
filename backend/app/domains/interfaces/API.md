# Interfaces API

| Method | Path | Permission | 원본 |
|---|---|---|---|
| GET | `/api/v1/interfaces` | `interfaces:read` | BusinessSystemIn |
| GET | `/api/v1/interfaces/topology` | `interfaces:read` | RTIMS MON_INTF_MAP |
| GET | `/api/v1/interfaces/namespaces` | `interfaces:read` | SAP InterfaceMonitor |

Namespace 응답은 SID, 인터페이스명, namespace, 방향, 송신·수신 시스템과 operation을 제공한다. 내부 WSDL URL은 반환하지 않는다.
