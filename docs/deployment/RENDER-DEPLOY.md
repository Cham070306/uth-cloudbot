# Hướng dẫn Deploy lên Render

## URL Production
https://uth-cloudbot.onrender.com

## Yêu cầu
- Tài khoản Render (free tier)
- Repo GitHub: https://github.com/Cham070306/uth-cloudbot

## Biến môi trường
| Biến | Giá trị | Ghi chú |
|------|---------|---------|
| DATA_BACKEND | local / firestore | local cho test |
| GEMINI_ENABLED | false / true | bật sau khi có key |
| GEMINI_API_KEY | secret | lấy từ Châm |
| GEMINI_MODEL | gemini-2.0-flash | |
| GOOGLE_CLOUD_PROJECT | uth-cloudbot-nhom22 | khi dùng Firestore |

## Deploy mới
1. Push code lên nhánh `feature/cl-01-cloud-run`
2. Vào Render → Manual Deploy → Deploy latest commit

## Rollback
1. Vào Render → Deploys
2. Tìm deploy cũ đang hoạt động
3. Click "Rollback to this deploy"

## Health check
GET https://uth-cloudbot.onrender.com/api/health

## Known Issues
- Free tier spin down sau 15 phút không dùng, request đầu tiên chậm ~50s
- Chưa có Firestore, đang dùng local data mock