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

Tất cả cấu hình API nằm **duy nhất** trong `src/js/config.js`:

- `ENV`: đổi giữa `"local"` (chạy Flask ở máy) và `"render"` (backend thật trên Render).
- `USE_MOCK`: đặt `true` để test giao diện bằng dữ liệu giả khi chưa có backend hoặc backend đang lỗi.
- `RESPONSE_FIELDS` / `REQUEST_FIELDS`: đổi tên field JSON nếu backend đặt tên khác (`message`, `answer`, `source`, `source_type`...).

Không cần sửa `script.js` hay `index.html` khi đổi backend — chỉ sửa `config.js`.

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
