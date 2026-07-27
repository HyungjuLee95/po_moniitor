# 환경 설정과 서버 증설

## 단일 관리 지점

루트 `.env`가 프론트와 백엔드의 로컬 설정 원본입니다. `.env.example`을 복사해 사용하며 실제 `.env`는 Git에 올리지 않습니다.

- `NEXT_PUBLIC_*`: 브라우저에 포함되어도 되는 값만 사용
- `DATABASE_URL`, `SECRET_KEY`, `SAP_PO_*`: 백엔드 전용 비밀값
- `PO_SERVERS_JSON`: 서버 목록과 서버별 기능

## 서버 추가

`PO_SERVERS_JSON` 배열에 다음 형식의 객체를 추가합니다.

```json
{
  "sid": "PON",
  "display_name": "PO New Server",
  "environment": "quality",
  "base_url": "https://po-new.internal.example",
  "port": 50000,
  "enabled": true,
  "capabilities": ["monitor", "channel-control", "collector"]
}
```

백엔드를 재시작하면 설정이 검증됩니다. 정상 서버는 bootstrap API에 포함되고 프론트 선택 목록에 자동 추가됩니다. 프론트 재빌드는 필요하지 않습니다.

## 허용값

- `sid`: 대문자로 시작하는 2~8자의 대문자·숫자
- `environment`: `production`, `quality`, `development`, `sandbox`
- `capabilities`: `monitor`, `channel-control`, `audit`, `collector`, `hrd`
- `port`: 1~65535

SID 중복이나 잘못된 값은 애플리케이션 시작 단계에서 오류로 처리합니다. 서버를 잠시 숨길 때는 삭제 대신 `enabled:false`를 사용합니다.

## BASE URL 기준

- 프론트 API 주소: `NEXT_PUBLIC_API_BASE_URL`
- 백엔드 공통 API prefix: `/api/v1`
- SAP PO 주소: 각 서버의 `base_url` + `port`

SAP PO URL은 백엔드에서만 사용하며 bootstrap 응답에서 제거됩니다.
