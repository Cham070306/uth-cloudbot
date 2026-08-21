# UTH CloudBot — Frontend (FE-01, FE-02)

Giao diện chatbot hỗ trợ sinh viên, kết nối backend Flask thật (Render).

## Cấu trúc thư mục

```
frontend/
├── public/
│   └── index.html        # Trang chính
├── src/
│   ├── css/style.css     # Toàn bộ style
│   └── js/
│       ├── config.js     # Cấu hình API — SỬA Ở ĐÂY khi backend đổi field/URL
│       └── script.js     # Logic chat, gọi API, hiển thị nguồn
├── tests/
│   └── checklist.md      # Checklist test thủ công
└── README.md
```

## Chạy thử trên máy (không cần server)

Mở trực tiếp `public/index.html` bằng trình duyệt. Không cần cài gì thêm.

## Cấu hình kết nối backend

Tất cả cấu hình API nằm **duy nhất** trong `src/js/config.js` — đã đối chiếu trực tiếp với code Python thật (không còn đoán field).

- `ENV`: đổi giữa `"local"` và `"render"`.
- `USE_MOCK`: `true` để test bằng dữ liệu giả khi backend lỗi/chưa sẵn sàng.
- Backend nhận field `message` khi hỏi (`routes/chat.py` cũng chấp nhận `question` để tương thích ngược).
- Backend trả `source` là **object** `{type, title, url}`, kèm 2 cờ `ai_generated` và `fallback_used` — dùng để xác định badge nguồn chính xác, không đoán qua từ khóa.
- Nút feedback gửi `{question, answer, vote: "up"|"down"}` theo đúng nhánh "legacy" mà `routes/feedback.py` hỗ trợ.
- Đăng nhập gọi thật `POST /api/auth/login` với `{username, password}`, nhận `access_token` — token này được gắn vào header `Authorization: Bearer ...` cho các câu hỏi dữ liệu cá nhân.
- **Tài khoản demo có sẵn:** `sv001` / `demo123` hoặc `sv002` / `demo123` (từ `data/sample/student_context.json`).

## ⚠️ Cần Nghĩa cấu hình trên Render

Backend mặc định chỉ cho phép CORS từ `http://localhost:5173` (`backend/config.py`). Khi frontend đã có URL GitHub Pages, **Nghĩa cần thêm URL đó vào biến môi trường `CORS_ORIGINS` trên Render**, nếu không trình duyệt sẽ chặn mọi request gọi API dù backend vẫn chạy bình thường.

## Tính năng đã hoàn thành

- Danh sách tin nhắn, ô nhập, nút gửi
- Kết nối API thật: `GET /api/health`, `POST /api/chat`, `POST /api/feedback`
- Trạng thái: đang tải, lỗi mạng/timeout (giữ nguyên câu hỏi gốc khi bấm Thử lại)
- Phân biệt nguồn câu trả lời: FAQ / Dữ liệu demo / Gemini AI / Fallback (badge màu riêng)
- Ghi chú bắt buộc khi trả lời từ Gemini: "Nội dung do AI tạo, chỉ dùng để tham khảo."
- Nút feedback 👍 / 👎
- Đăng nhập demo (giả lập, không xác thực thật) + hiển thị tên/MSSV trong sidebar
- Responsive desktop và mobile

## Lưu ý

- `source` và `source_type` từ backend hiện đang được suy luận/dự phòng nếu backend không trả đúng field — xem hàm `inferSourceType` trong `config.js`.
- Đăng nhập demo chỉ lưu dữ liệu trong bộ nhớ trình duyệt phiên hiện tại, không gửi lên server, không có xác thực thật.
