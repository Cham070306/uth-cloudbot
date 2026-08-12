# Bàn giao phần Châm và Huy cho Cloud/DevOps

## Phạm vi đã sẵn sàng

- Huy: FE-02 LIVE/MOCK, health, chat, feedback, timeout/retry/reset, render an toàn, đăng nhập demo, dữ liệu cá nhân, xác nhận note/reminder và responsive.
- Châm: BE-02 intent router, FAQ demo, Personal Assistant, repository abstraction DB-01, local persistence trong phiên chạy, Firestore adapter, seed và API validation thống nhất.

## Kiến trúc và chạy local

Frontend gọi Flask `/api/*`. Route gọi service; service truy cập dữ liệu qua `DataRepository`. `DATA_BACKEND=local` dùng JSON demo/bộ nhớ; `firestore` dùng Application Default Credentials.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DATA_BACKEND = "local"
$env:PORT = "8080"
python app.py
```

Terminal khác: `python -m http.server 5173 --directory frontend`, rồi mở `http://localhost:5173/public/`. Tài khoản demo: `sv001` / `demo123`.

## Biến môi trường

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `PORT` | `8080` | Port HTTP |
| `CORS_ORIGINS` | localhost/127.0.0.1:5173 | Danh sách cách nhau bằng dấu phẩy |
| `DATA_BACKEND` | `local` | `local` hoặc `firestore` |
| `GOOGLE_CLOUD_PROJECT` | rỗng | Bắt buộc với Firestore |
| `FIRESTORE_COLLECTION_PREFIX` | `uth_cloudbot` | Prefix collection |

Seed/test: `python -m scripts.seed_data` và `python -m pytest -q` trong `backend`. Seed upsert nên chạy lặp an toàn. Local có 30 FAQ, 10 documents và dữ liệu lịch/bài tập/thi/thông báo. Xem schema ở `docs/architecture/DATABASE-SCHEMA.md`, API ở `docs/api/PERSONAL-ASSISTANT.md` và Postman trong `backend/postman/`.

## Mock và hạn chế

- Toàn bộ FAQ, tài khoản/token, lịch, bài tập, thi, thông báo, tài liệu là demo chưa được UTH kiểm chứng.
- Token cố định/mật khẩu rõ chỉ dùng local; production cần Identity provider và secret ngoài Git.
- Local repository không bền sau restart; Firestore cần ADC. Reminder scheduler chỉ chạy khi đọc reminders.
- Không có Gemini, crawling, dữ liệu thật hay triển khai Cloud Run trong phạm vi này.

## Checklist cho Nghĩa

- Entry point `backend/app.py`, bind `0.0.0.0`, đọc `PORT`, debug tắt; health `GET /api/health` không cần auth.
- Cấu hình `CORS_ORIGINS`, `DATA_BACKEND=firestore`, project và prefix.
- Dùng Workload Identity/ADC; không đặt service-account JSON trong image/repo.
- Chạy `backend/scripts/seed_data.py` sau khi cấu hình Firestore.
- Tạo auth/signing secret bên ngoài repo khi thay auth demo.
