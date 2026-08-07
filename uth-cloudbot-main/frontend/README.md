# Frontend — UTH CloudBot

Giao diện chatbot hỗ trợ sinh viên, dựng theo bản Figma "AI Chatbot (Community)".
Thuần HTML/CSS/JS, chưa cần build tool.

## Cấu trúc

```
frontend/
├── public/
│   └── index.html      # entry point, mở file này trong trình duyệt
├── src/
│   ├── css/style.css   # design tokens + toàn bộ style (theo Figma)
│   └── js/script.js    # logic chat + tích hợp API (FE-02)
└── tests/
```

## Chạy thử local

```bash
cd frontend
python3 -m http.server 5500
# mở http://localhost:5500/public/index.html
```

## FE-02 — Tích hợp API

Trong `src/js/script.js`, đầu file có phần cấu hình:

```js
const USE_MOCK   = true;   // đổi thành false khi backend sẵn sàng
const API_BASE    = "";     // điền domain backend, vd "https://xxx.a.run.app"
const TIMEOUT_MS   = 12000;  // thời gian chờ trước khi báo timeout
```

- **`USE_MOCK = true`** (mặc định): dùng dữ liệu giả `mockKnowledgeBase`, không gọi
  mạng — để demo/test UI khi backend chưa xong.
- **`USE_MOCK = false`**: gọi thật `POST /api/chat` và `POST /api/feedback`.

### Hợp đồng API kỳ vọng (báo team backend biết để khớp)

**POST `/api/chat`**
```json
// request
{ "question": "Học phí kỳ này bao nhiêu?" }

// response — câu trả lời hợp lệ
{
  "invalid": false,
  "paragraphs": ["Học phí học kỳ này..."],
  "list": ["Mức phí: ...", "Hạn đóng: ..."],
  "sources": [{ "label": "Thông báo học phí HK1", "url": "https://..." }]
}

// response — không hiểu câu hỏi
{ "invalid": true }
```

**POST `/api/feedback`**
```json
{ "question": "...", "answer": "...", "vote": "up" }
```

### Các trạng thái lỗi đã xử lý ở frontend

- **Loading**: hiện dấu ba chấm nhảy trong lúc chờ.
- **Timeout**: dùng `AbortController`, huỷ request sau `TIMEOUT_MS` (mặc định 12s),
  hiện banner riêng "Yêu cầu quá thời gian chờ".
- **Lỗi mạng / server lỗi**: bắt lỗi `fetch` hoặc `res.ok === false`, hiện banner
  kèm nút "Thử lại" (gửi lại đúng câu hỏi vừa thất bại).
- **Câu hỏi rỗng**: chặn submit, hiện dòng cảnh báo đỏ dưới ô nhập, không gọi API.
- Test nhanh ở chế độ mock: gõ câu hỏi chứa chữ **"lỗi mạng"** để giả lập lỗi mạng,
  hoặc chứa chữ **"timeout"** để giả lập hết thời gian chờ.

## Việc còn lại

- Backend đội 2 cần dựng đúng 2 endpoint trên (`backend/app.py`).
- Khi có domain thật, điền vào `API_BASE` và đổi `USE_MOCK = false`.
