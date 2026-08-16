# Hướng dẫn Nghĩa cấu hình Render, Firestore và Gemini 3.5

## 1. Phạm vi phụ trách

Nghĩa phụ trách phần Cloud/DevOps:

- Cấu hình backend UTH CloudBot trên Render Free.
- Kết nối backend Render với Firestore của project `uth-cloudbot`.
- Cấu hình Gemini API bằng secret trên Render.
- Redeploy, kiểm tra log và xác minh dữ liệu còn sau restart.
- Lưu ảnh cấu hình và kết quả kiểm thử làm minh chứng.

Châm phụ trách hỗ trợ khi có lỗi code Gemini, fallback, repository hoặc Firestore adapter. Huy phụ trách frontend, URL API, CORS và kiểm tra responsive.

## 2. Thông tin đã xác nhận

```text
Render service: uth-cloudbot-backend
Backend URL: https://uth-cloudbot.onrender.com
Health check: https://uth-cloudbot.onrender.com/api/health
Google Cloud Project ID: uth-cloudbot
Firestore database: (default)
Collection prefix: uth_cloudbot
Gemini model: gemini-3.5-flash
Gemini timeout: 30 giây
```

Firestore hiện đã được seed dữ liệu demo:

| Collection | Số document |
|---|---:|
| `uth_cloudbot_faqs` | 150 |
| `uth_cloudbot_documents` | 30 |
| `uth_cloudbot_students` | 10 |
| `uth_cloudbot_schedules` | 60 |
| `uth_cloudbot_assignments` | 35 |
| `uth_cloudbot_exams` | 20 |
| `uth_cloudbot_announcements` | 30 |
| `uth_cloudbot_conversations` | 19 tại thời điểm bàn giao |

Kết quả kiểm thử local tại thời điểm bàn giao:

```text
109 tests passed
FAQ evaluation: 300/300
Accuracy: 100%
```

## 3. Nguyên tắc bảo mật bắt buộc

- Không commit `credential.json` lên GitHub.
- Không ghi Gemini API key vào `render.yaml`, `.env.example` hoặc source code.
- Không gửi nội dung private key trong nhóm chat.
- Chỉ nhập credential vào Secret File của Render.
- Chỉ nhập Gemini API key trong Render Environment.
- Khi chụp minh chứng, phải che API key và nội dung credential.

## 4. Điều kiện trước khi cấu hình

Chỉ thực hiện sau khi nhánh chứa dữ liệu mới và Gemini 3.5 đã được review, merge và push lên nhánh mà Render đang deploy.

Trong Render Dashboard, kiểm tra service đang liên kết đúng repository và đúng branch. Nếu Render vẫn deploy commit cũ, cấu hình Environment đúng nhưng code mới vẫn chưa được sử dụng.

## 5. Thêm credential Firestore bằng Secret File

1. Mở <https://dashboard.render.com/>.
2. Chọn service `uth-cloudbot-backend`.
3. Chọn **Environment** ở menu bên trái.
4. Kéo xuống phần **Secret Files**.
5. Bấm **Add Secret File**.
6. Nhập filename:

```text
credential.json
```

7. Nhận nội dung credential từ Trâm qua kênh riêng hoặc cùng Trâm nhập trực tiếp trên Render.
8. Dán toàn bộ JSON vào ô **Contents**.
9. Không dán JSON vào Environment Variable thông thường.

Render cung cấp file tại đường dẫn runtime:

```text
/etc/secrets/credential.json
```

## 6. Cấu hình Environment cho Firestore

Trong **Environment Variables**, thêm hoặc sửa để chỉ còn một dòng cho mỗi key:

```env
DATA_BACKEND=firestore
GOOGLE_CLOUD_PROJECT=uth-cloudbot
FIRESTORE_COLLECTION_PREFIX=uth_cloudbot
GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/credential.json
```

Không dùng đường dẫn Windows `D:\...\credential.json` trên Render vì đường dẫn đó chỉ tồn tại trên máy Trâm.

## 7. Cấu hình Gemini 3.5

Trong **Environment Variables**, thêm hoặc sửa:

```env
GEMINI_ENABLED=true
GEMINI_API_KEY=<nhập API key mới trực tiếp trên Render>
GEMINI_MODEL=gemini-3.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

Lưu ý:

- Không nhập ký tự `<` và `>` vào giá trị thật.
- Phải dùng API key mới, còn hiệu lực và có quyền truy cập model.
- Không chụp hoặc gửi giá trị `GEMINI_API_KEY`.
- Nếu có hai biến trùng tên, xóa biến dư và giữ một giá trị đúng.

## 8. CORS

Thêm URL frontend production sau khi Huy cung cấp. Trong thời gian kiểm tra local, có thể dùng:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Khi có URL frontend public, nối thêm URL đó, phân cách bằng dấu phẩy. Ví dụ:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://<frontend-domain>
```

Không để dấu `/` ở cuối URL nếu backend đang so khớp origin theo chuỗi chính xác.

## 9. Lưu và deploy

Sau khi nhập Secret File và Environment Variables:

1. Bấm **Save Changes**.
2. Chọn **Save, rebuild, and deploy**.
3. Mở trang **Deploys** hoặc **Logs**.
4. Chờ deploy có trạng thái **Live**.

Không chỉ chọn **Save only**. Không chỉ restart service sau khi vừa thay đổi Environment; phải deploy để cấu hình mới có hiệu lực.

## 10. Kiểm tra log

Trong Render Logs, kiểm tra các lỗi:

```text
Cannot initialize Firestore
DefaultCredentialsError
PermissionDenied
File not found: /etc/secrets/credential.json
missing_api_key
authentication_error
invalid_model
quota_exceeded
timeout
network_error
```

Nếu log có secret, không chụp màn hình và không gửi công khai.

## 11. Kiểm tra health

Mở:

<https://uth-cloudbot.onrender.com/api/health>

Kết quả yêu cầu:

```json
{
  "service": "uth-cloudbot-backend",
  "status": "ok"
}
```

## 12. Kiểm tra Firestore từ Render

Mở PowerShell và chạy:

```powershell
$body = @{
    message = "Kiểm tra Render ghi Firestore sau khi cấu hình"
} | ConvertTo-Json

$result = Invoke-RestMethod `
    -Method Post `
    -Uri "https://uth-cloudbot.onrender.com/api/chat" `
    -ContentType "application/json" `
    -Body $body

$result | ConvertTo-Json -Depth 10
```

Sau đó kiểm tra Firebase Console:

```text
Firestore
→ Data
→ uth_cloudbot_conversations
```

Trước khi bàn giao có 19 conversation. Sau khi gửi một câu mới, số document phải tăng. Mở document mới nhất và xác nhận nội dung câu hỏi đúng với câu vừa gửi.

Nếu không tăng:

- Kiểm tra `DATA_BACKEND` có đúng `firestore`.
- Kiểm tra Project ID `uth-cloudbot`.
- Kiểm tra đường dẫn `/etc/secrets/credential.json`.
- Kiểm tra quyền `Cloud Datastore User` của service account.
- Kiểm tra Render Logs.

## 13. Kiểm tra dữ liệu sau restart

1. Ghi lại ID conversation vừa tạo.
2. Vào **Deploys**.
3. Chọn **Manual Deploy → Restart service**.
4. Chờ service trở lại **Live**.
5. Kiểm tra conversation cũ vẫn còn trong Firestore.
6. Gửi thêm một câu hỏi và xác nhận backend tiếp tục ghi được.

Nếu dữ liệu vẫn còn sau restart, Firestore persistence đạt yêu cầu.

## 14. Kiểm tra Gemini 3.5

Dùng câu kiến thức mở, tránh câu đã có trong FAQ:

```powershell
$body = @{
    message = "Phân tích ưu và nhược điểm của kiến trúc multi-cloud trong doanh nghiệp."
} | ConvertTo-Json

$result = Invoke-RestMethod `
    -Method Post `
    -Uri "https://uth-cloudbot.onrender.com/api/chat" `
    -ContentType "application/json" `
    -Body $body

$result | ConvertTo-Json -Depth 10
```

Kết quả thành công phải có:

```json
{
  "ai_generated": true,
  "fallback_used": false,
  "source": {
    "type": "gemini",
    "title": "Gemini AI"
  }
}
```

Nếu kết quả là fallback, kiểm tra Render Logs:

| Lý do | Cách xử lý |
|---|---|
| `missing_api_key` | Kiểm tra biến `GEMINI_API_KEY` |
| `authentication_error` | Key sai, bị thu hồi hoặc không có quyền |
| `invalid_model` | Key/project không hỗ trợ `gemini-3.5-flash` hoặc code deploy còn cũ |
| `quota_exceeded` | Hết quota hoặc model yêu cầu billing phù hợp |
| `timeout` | Tăng timeout hoặc thử lại sau khi Render đã warm up |
| `network_error` | Kiểm tra kết nối và thử deploy lại |

Chỉ để chẩn đoán, có thể thử tạm `gemini-2.5-flash`. Nếu 2.5 hoạt động nhưng 3.5 không hoạt động thì lỗi nằm ở quyền model/quota, không phải luồng chatbot.

## 15. Kiểm tra rule-based không gọi Gemini

Gửi một câu đã có FAQ, ví dụ:

```text
Làm thế nào để đăng ký học lại?
```

Kết quả phải ưu tiên dữ liệu hệ thống, không phải Gemini. Sau đó gửi câu dữ liệu cá nhân và xác nhận chatbot đọc đúng Firestore, không gửi dữ liệu cá nhân sang Gemini.

## 16. Minh chứng Nghĩa cần bàn giao

Lưu các ảnh sau, che toàn bộ secret:

1. Render service ở trạng thái **Live**.
2. Danh sách tên Environment Variables, không hiển thị giá trị secret.
3. Secret File có filename `credential.json`, không hiển thị Contents.
4. Health check thành công.
5. Gemini trả `ai_generated=true` và `source.type=gemini`.
6. FAQ trả nguồn rule-based.
7. Firestore có conversation mới từ Render.
8. Conversation vẫn còn sau restart.
9. Render Logs không có lỗi credential/Gemini.
10. Kết quả smoke test cloud.

Đặt minh chứng vào:

```text
docs/evidence/cloud/
```

Không thêm file secret vào thư mục minh chứng.

## 17. Checklist hoàn thành

- [ ] Code mới đã merge và Render deploy đúng commit.
- [ ] Secret File `credential.json` đã thêm vào Render.
- [ ] `DATA_BACKEND=firestore`.
- [ ] `GOOGLE_CLOUD_PROJECT=uth-cloudbot`.
- [ ] `FIRESTORE_COLLECTION_PREFIX=uth_cloudbot`.
- [ ] `GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/credential.json`.
- [ ] `GEMINI_ENABLED=true`.
- [ ] Gemini API key mới đã nhập trên Render.
- [ ] `GEMINI_MODEL=gemini-3.5-flash`.
- [ ] `GEMINI_TIMEOUT_SECONDS=30`.
- [ ] CORS đã có URL frontend.
- [ ] Health check HTTP 200.
- [ ] Gemini trả `source.type=gemini`.
- [ ] FAQ vẫn ưu tiên rule-based.
- [ ] Render ghi được conversation vào Firestore.
- [ ] Dữ liệu còn sau restart.
- [ ] Đã lưu đủ minh chứng và che secret.

## 18. Nội dung Nghĩa gửi lại nhóm

```text
Đã hoàn thành cấu hình Render cho UTH CloudBot:

- Backend URL: https://uth-cloudbot.onrender.com
- Firestore project: uth-cloudbot
- DATA_BACKEND: firestore
- Gemini model: gemini-3.5-flash
- Health check: đạt
- Rule-based: đạt
- Gemini: đạt/chưa đạt (ghi rõ lý do nếu chưa đạt)
- Firestore read/write: đạt
- Dữ liệu sau restart: còn
- CORS frontend: đã cấu hình theo URL ...
- Minh chứng: docs/evidence/cloud/

Không có API key hoặc credential được đưa lên GitHub.
```
