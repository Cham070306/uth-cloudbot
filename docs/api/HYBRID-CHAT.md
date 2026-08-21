# API chat hybrid Rule-based + Gemini

`POST /api/chat` xử lý theo thứ tự cố định: dữ liệu cá nhân demo, FAQ/rule-based, Gemini cho kiến thức mở, rồi fallback. Câu hỏi cá nhân và FAQ đã khớp không được gửi tới Gemini. Tất cả dữ liệu UTH hiện có chỉ là demo, không phải nguồn chính thức.

## Cấu hình

Gemini mặc định tắt. Đặt các biến sau trong PowerShell hoặc Environment Secrets của Render:

```powershell
$env:GEMINI_ENABLED = "true"
$env:GEMINI_API_KEY = "<secret>"
$env:GEMINI_MODEL = "gemini-3.5-flash"
$env:GEMINI_TIMEOUT_SECONDS = "10"
```

Không commit API key. `GEMINI_MODEL` không có mặc định cố định để tránh phụ thuộc model đã hết vòng đời. Thiếu key/model, timeout không hợp lệ, quota 429, lỗi xác thực, lỗi mạng hoặc response rỗng đều kích hoạt fallback; API vẫn trả HTTP 200.

## Response mẫu

FAQ:

```json
{
  "answer": "Tra cứu học phí trên cổng sinh viên...",
  "intent": "faq",
  "source": {"type": "sample", "title": "Dữ liệu FAQ mẫu", "url": null},
  "ai_generated": false,
  "fallback_used": false
}
```

Gemini:

```json
{
  "answer": "Điện toán đám mây là mô hình cung cấp tài nguyên CNTT qua mạng...",
  "intent": "knowledge",
  "source": {"type": "gemini", "title": "Gemini AI", "url": null},
  "ai_generated": true,
  "fallback_used": false
}
```

Fallback:

```json
{
  "answer": "Đây là phản hồi minh họa của UTH CloudBot...",
  "intent": "knowledge",
  "source": {"type": "fallback", "title": "Phản hồi dự phòng", "url": null},
  "ai_generated": false,
  "fallback_used": true
}
```

Response thực tế còn luôn có `invalid`, `paragraphs`, `list`, `sources`, `data`; route bổ sung `latency_ms` và `message_id`.

Yêu cầu xem dữ liệu cá nhân khi chưa đăng nhập là phản hồi hệ thống, không phải fallback Gemini:

```json
{
  "intent": "personal_schedule",
  "source": {"type": "system", "title": "Yêu cầu đăng nhập", "url": null},
  "requires_authentication": true,
  "ai_generated": false,
  "fallback_used": false
}
```

## Chạy test

```powershell
cd backend
python -m pip install -r requirements.txt
python -m pytest -q
```

Unit test mock toàn bộ Gemini và không gọi API thật.
