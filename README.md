# UTH CloudBot

UTH CloudBot là dự án chatbot hỗ trợ sinh viên Trường Đại học Giao thông vận tải TP.HCM (UTH). Phiên bản hiện tại gồm giao diện frontend và backend BE-01 chạy local bằng dữ liệu mock.

> Nội dung mock chỉ phục vụ phát triển và kiểm thử, không phải nguồn thông tin chính thức của UTH.

## Trạng thái hiện tại

- FE-01: giao diện chatbot HTML/CSS/JavaScript.
- BE-01: Flask API cơ bản với health check, chat mock và tiếp nhận feedback.
- Dữ liệu thật UTH, database, Firestore, Gemini và triển khai cloud chưa được tích hợp.

## Cấu trúc dự án

```text
uth-cloudbot/
├── frontend/                 # Giao diện chatbot
├── backend/
│   ├── app.py                # Flask application factory và error handlers
│   ├── config.py             # PORT, CORS và giới hạn request
│   ├── routes/               # Ba endpoint BE-01
│   ├── services/             # Mock chat service
│   ├── data/                 # Dữ liệu minh họa
│   ├── tests/                # Pytest API tests
│   └── postman/              # Postman collection
└── README.md
```

## Chạy backend BE-01

Yêu cầu Python 3.11 trở lên. Mở PowerShell tại thư mục dự án:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Backend mặc định chạy tại `http://localhost:8080`.

## API BE-01

| Method | Endpoint | Chức năng |
|---|---|---|
| `GET` | `/api/health` | Kiểm tra trạng thái backend |
| `POST` | `/api/chat` | Nhận câu hỏi và trả phản hồi mock |
| `POST` | `/api/feedback` | Xác nhận feedback, không lưu database |

Ví dụ kiểm tra chat bằng PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8080/api/chat" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body (@{ message = "Sinh viên có thể xem thông báo ở đâu?" } | ConvertTo-Json)
```

Contract, validation, CORS và ví dụ response đầy đủ được mô tả trong [backend/README.md](backend/README.md).

## Chạy kiểm thử

Sau khi kích hoạt virtual environment và cài dependency:

```powershell
cd backend
python -m pytest -q
```

Bộ test kiểm tra ba endpoint, validation, lỗi JSON, giới hạn request, CORS và khả năng tương thích với frontend hiện tại.

Để kiểm thử thủ công, import collection:

```text
backend/postman/UTH-CloudBot-BE01.postman_collection.json
```

Biến `baseUrl` trong collection mặc định là `http://localhost:8080`.

## Kết nối frontend với backend local

Trong `frontend/src/js/script.js`, đặt:

```javascript
const USE_MOCK = false;
const API_BASE = "http://localhost:8080";
```

Backend mặc định cho phép CORS từ `http://localhost:5173` và `http://127.0.0.1:5173`.

## Thành viên

- Thành viên 1: Frontend.
- Thành viên 2: Backend và dữ liệu.
- Thành viên 3: Cloud, triển khai và kiểm thử.

## Phạm vi chưa triển khai

BE-01 không bao gồm intent router thật, dữ liệu thật UTH, Firestore, Gemini, database, web crawling, Docker, Cloud Run, đăng nhập hoặc dữ liệu cá nhân sinh viên.
