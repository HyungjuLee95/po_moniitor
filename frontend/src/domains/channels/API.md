# Channels API

목록·상세·통계는 `/channels`, `/inventory`, `/detail`, `/statistics`, `/message-history`를 사용한다. 제어 화면은 `/control`, `/batch-control-stream`, `/bulk-export`, `/bulk-preview`를 사용하며 SSE와 인증 Blob/FormData를 처리한다.

- 채널 컨트롤: `/control`, `/batch-control-stream`
- 채널 대량 변경: `/bulk-export?component_id=`, `/bulk-preview`
