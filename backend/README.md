# UTH CloudBot — BE-01

Backend Flask cơ bản chạy local với đúng ba endpoint health, chat mock và feedback không lưu trữ. Nội dung mock chỉ dùng để minh họa, **không phải nguồn thông tin chính thức của UTH**.

## Yêu cầu và cài đặt

- Python 3.11 trở lên

Từ thư mục `backend` trên Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Chạy server

```powershell
python app.py
```

Backend mặc định chạy tại `http://localhost:8080`. Có thể đặt biến môi trường cho phiên PowerShell hiện tại:

```powershell
$env:PORT = "8080"
$env:CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
python app.py
```

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `PORT` | `8080` | Cổng HTTP local |
| `CORS_ORIGINS` | hai origin Vite local ở trên | Danh sách origin, phân tách bằng dấu phẩy |

Server không bật debug và giới hạn request ở 16 KiB.

## API contract

### `GET /api/health`

HTTP 200:

```json
{"status":"ok","service":"uth-cloudbot-backend"}
```

### `POST /api/chat`

Request chuẩn:

```json
{"message":"Sinh viên có thể xem thông báo ở đâu?"}
```

`message` phải là chuỗi không rỗng sau khi trim và tối đa 2.000 ký tự. Để tương thích FE-01 hiện tại, `question` được chấp nhận như alias của `message`.

HTTP 200 luôn có các trường chuẩn `answer`, `intent`, `source`, `updated_at`, `latency_ms`. Ngoài ra có `invalid`, `paragraphs`, `list`, `sources` để renderer FE-01 hiện tại sử dụng:

```json
{
  "answer": "Đây là phản hồi minh họa...",
  "intent": "unknown",
  "source": {"type":"mock","title":"Dữ liệu mẫu BE-01","url":null},
  "updated_at": null,
  "latency_ms": 0,
  "invalid": false,
  "paragraphs": ["Đây là phản hồi minh họa..."],
  "list": [],
  "sources": [{"label":"Dữ liệu mẫu BE-01","url":null}]
}
```

### `POST /api/feedback`

Request chuẩn:

```json
{"message_id":"demo-message-001","helpful":true}
```

HTTP 200:

```json
{"status":"received","message_id":"demo-message-001","helpful":true}
```

`helpful` phải là boolean thật. Payload FE-01 `{question, answer, vote}` cũng được hỗ trợ (`vote` là `up` hoặc `down`). Feedback chỉ được xác nhận, không lưu vào bộ nhớ hay database.

Mọi lỗi trả JSON dạng `{"error":{"code":"...","message":"..."}}`; gồm 400, 404, 405, 413 và 500.

## Kiểm thử

```powershell
python -m pytest -q
```

Import `postman/UTH-CloudBot-BE01.postman_collection.json` vào Postman, chạy server rồi chạy collection. Biến `baseUrl` mặc định là `http://localhost:8080`. Collection chỉ có năm request thuộc BE-01.

## Kết nối FE-01 local

Trong `frontend/src/js/script.js`, FE hiện vẫn ở mock mode. Khi tích hợp thủ công, đặt `USE_MOCK = false` và `API_BASE = "http://localhost:8080"`. Backend đã cho phép `http://localhost:5173` và `http://127.0.0.1:5173`; thay danh sách bằng `CORS_ORIGINS` nếu frontend dùng origin khác.

## Known issues và công việc tiếp theo

- Mock luôn trả cùng một nội dung và `intent: "unknown"`; không phân loại câu hỏi thật.
- Alias tương thích FE-01 sẽ được giữ cho đến khi frontend thống nhất contract chuẩn BE-01.
- Firestore, Gemini, dữ liệu thật đã kiểm chứng của UTH, intent router, tài khoản sinh viên và triển khai cloud thuộc giai đoạn sau, chưa được triển khai.
- Khi sang giai đoạn được phê duyệt, có thể thay `services/mock_chat_service.py` bằng service dữ liệu thật mà không đổi các trường response chuẩn.
