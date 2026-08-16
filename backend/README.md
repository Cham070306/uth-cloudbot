# UTH CloudBot — BE-02 và DB-01

Backend Flask chạy theo mô hình hybrid Rule-based + Gemini. Nội dung FAQ, tài khoản và dữ liệu cá nhân hiện tại chỉ dùng để minh họa, **không phải nguồn thông tin chính thức của UTH**.

Cơ sở tri thức hiện có 150 FAQ demo (yêu cầu tối thiểu ban đầu: 30), kèm 300 cách hỏi đánh giá retrieval. Chạy `python -m scripts.evaluate_faq` để xem accuracy mà không gọi Gemini.

Dữ liệu local còn có 10 sinh viên demo, 60 lịch học, 35 bài tập, 20 kỳ thi, 30 thông báo và 30 tài liệu. Toàn bộ là dữ liệu giả lập; endpoint `GET /api/documents` trả tài liệu demo và hỗ trợ lọc bằng query `category`.

BE-01 mở rộng bổ sung Intent Router và hơn 100 cách hỏi FAQ cho `/api/chat`. Intent `knowledge` và `unknown` chỉ gọi Gemini khi không khớp FAQ; lịch học, lịch thi và tài liệu tiếp tục dùng fallback khi không có dữ liệu phù hợp.

Backend hiện còn có chế độ trợ lý học tập cá nhân dựa trên tài khoản và dữ liệu hoàn toàn giả lập: lịch học, bài tập E-learning, deadline, kiểm tra, thông báo, note và reminder có xác nhận. Xem [tài liệu trợ lý cá nhân](../docs/api/PERSONAL-ASSISTANT.md).

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
| `DATA_BACKEND` | `local` | `local` hoặc `firestore` |
| `GOOGLE_CLOUD_PROJECT` | rỗng | Project khi dùng Firestore |
| `FIRESTORE_COLLECTION_PREFIX` | `uth_cloudbot` | Prefix collection |
| `GEMINI_ENABLED` | `false` | Bật/tắt tầng trả lời Gemini |
| `GEMINI_API_KEY` | rỗng | API key Gemini; chỉ cấu hình bằng secret môi trường |
| `GEMINI_MODEL` | rỗng | Tên model Gemini đang được tài khoản hỗ trợ |
| `GEMINI_TIMEOUT_SECONDS` | `10` | Timeout dương theo giây; giá trị sai tự về 10 |

Local repository là mặc định và không cần Google credential. Conversation, feedback, note và reminder đều đi qua repository abstraction. Chạy seed idempotent bằng `python -m scripts.seed_data`; schema ở `docs/architecture/DATABASE-SCHEMA.md`.

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

HTTP 200 luôn có các trường chuẩn `answer`, `intent`, `source`, `ai_generated`, `fallback_used`, `invalid`, `paragraphs`, `list`, `sources`, `data`, `latency_ms` và `message_id`. Rule-based luôn được ưu tiên: dữ liệu cá nhân, FAQ, sau đó mới Gemini cho intent `knowledge`/`unknown`; Gemini không khả dụng sẽ trả fallback an toàn. Gemini không được dùng để tạo thông tin UTH chính thức.

```json
{
  "answer": "Đây là phản hồi minh họa...",
  "intent": "unknown",
  "source": {"type":"fallback","title":"Phản hồi dự phòng","url":null},
  "ai_generated": false,
  "fallback_used": true,
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

Các test mock hoàn toàn Gemini, không cần API key và không tiêu thụ quota. Cấu hình local mẫu nằm tại `../.env.example`; ứng dụng không tự nạp file `.env`, vì vậy cần đặt biến môi trường trong shell hoặc nền tảng deploy. Xem thêm [API chat hybrid](../docs/api/HYBRID-CHAT.md).

Import `postman/UTH-CloudBot-BE01.postman_collection.json` vào Postman, chạy server rồi chạy collection. Biến `baseUrl` mặc định là `http://localhost:8080`; collection có sẵn request FAQ, kiến thức mở, fallback và dữ liệu cá nhân demo.

## Kết nối FE-01 local

Trong `frontend/src/js/script.js`, FE hiện vẫn ở mock mode. Khi tích hợp thủ công, đặt `USE_MOCK = false` và `API_BASE = "http://localhost:8080"`. Backend đã cho phép `http://localhost:5173` và `http://127.0.0.1:5173`; thay danh sách bằng `CORS_ORIGINS` nếu frontend dùng origin khác.

## Known issues và công việc tiếp theo

- Fallback hiện dùng nội dung demo chung và không phải nguồn thông tin UTH chính thức.
- Alias tương thích FE-01 sẽ được giữ cho đến khi frontend thống nhất contract chuẩn BE-01.
- Gemini phụ thuộc API key, model hợp lệ, mạng và quota của môi trường deploy; khi lỗi hệ thống vẫn trả fallback.
- Chưa có dữ liệu thật đã kiểm chứng của UTH; không dùng response AI như thông báo chính thức.
