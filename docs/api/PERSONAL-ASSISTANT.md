# UTH CloudBot - Backend trợ lý học tập cá nhân

Tài liệu này mô tả phần mở rộng tuần tự trên backend BE-01. Toàn bộ hồ sơ, lịch học, bài tập, kỳ thi và thông báo là dữ liệu demo, không phải dữ liệu sinh viên UTH thật. Học kỳ demo `2026-1` dùng mốc `2026-08-17` đến `2026-12-20` theo múi giờ `Asia/Ho_Chi_Minh`.

## Tài khoản demo

| Username | Password | Token |
|---|---|---|
| `sv001` | `demo123` | `demo-token-sv001` |
| `sv002` | `demo123` | `demo-token-sv002` |
| `sv003` | `demo123` | `demo-token-sv003` |
| `sv004` | `demo123` | `demo-token-sv004` |
| `sv005` | `demo123` | `demo-token-sv005` |
| `sv006` | `demo123` | `demo-token-sv006` |
| `sv007` | `demo123` | `demo-token-sv007` |
| `sv008` | `demo123` | `demo-token-sv008` |
| `sv009` | `demo123` | `demo-token-sv009` |
| `sv010` | `demo123` | `demo-token-sv010` |

Đăng nhập bằng `POST /api/auth/login`, sau đó gửi token trong header:

```http
Authorization: Bearer demo-token-sv001
```

Token cố định và mật khẩu rõ chỉ được dùng cho bản demo local. Không sử dụng cách này với dữ liệu thật.

## API cá nhân

| Method | Endpoint | Chức năng |
|---|---|---|
| `GET` | `/api/me` | Hồ sơ tài khoản hiện tại |
| `GET` | `/api/me/schedule` | Lịch học; hỗ trợ query `from`, `to` |
| `GET` | `/api/me/assignments` | Bài tập; hỗ trợ query `status` |
| `GET` | `/api/me/assignments/upcoming` | Deadline trong 72 giờ |
| `GET` | `/api/me/exams` | Bài kiểm tra và kỳ thi |
| `GET` | `/api/me/announcements?unread=true` | Thông báo cá nhân |
| `GET` | `/api/documents?category=...` | Tài liệu demo công khai, có thể lọc category |
| `GET/POST` | `/api/me/notes` | Danh sách hoặc tạo note chờ xác nhận |
| `POST` | `/api/me/notes/{id}/confirm` | Xác nhận note |
| `POST` | `/api/me/notes/{id}/cancel` | Hủy note |
| `GET/POST` | `/api/me/reminders` | Danh sách hoặc tạo reminder chờ xác nhận |
| `POST` | `/api/me/reminders/{id}/confirm` | Xác nhận reminder |
| `POST` | `/api/me/reminders/{id}/complete` | Đánh dấu hoàn thành |
| `POST` | `/api/me/reminders/{id}/cancel` | Hủy reminder |

Khi đọc danh sách reminder, backend kiểm tra các reminder `scheduled` đã đến hạn và chuyển chúng sang `sent`. Đây là scheduler mô phỏng cho môi trường local.

`remind_at` bắt buộc là ISO-8601 có múi giờ, ví dụ `2026-08-13T20:00:00+07:00` hoặc hậu tố `Z`. Backend chuẩn hóa về `Asia/Ho_Chi_Minh`; frontend yêu cầu người dùng chọn thời gian tương lai trước khi xác nhận.

## Chat cá nhân hóa

`POST /api/chat` giữ nguyên contract BE-01 và nhận thêm header đăng nhập. Các intent cá nhân gồm:

- `personal_schedule`
- `personal_assignment`
- `personal_deadline`
- `personal_exam`
- `personal_announcement`
- `create_note`
- `create_reminder`

Ví dụ:

```http
POST /api/chat
Authorization: Bearer demo-token-sv001
Content-Type: application/json

{"message":"Tuần này tôi học môn gì?"}
```

Response cá nhân có thêm `data.items`. Nếu câu hỏi cần dữ liệu cá nhân nhưng không có token, response có `requires_authentication: true`.

Mọi response chat còn có `message_id` để liên kết conversation với feedback. Conversation và feedback được ghi qua repository abstraction; local chỉ tồn tại trong vòng đời tiến trình.

Yêu cầu tạo note hoặc reminder trả `requires_confirmation: true`. Client phải hiển thị bước xác nhận rồi mới gọi endpoint tạo và xác nhận tương ứng.

Hồ sơ `GET /api/me` giữ các trường cũ và bổ sung dữ liệu demo như `student_code`, `faculty`, `cohort`, `academic_year`, `phone_demo`, `enrollment_status`, `advisor`, `accumulated_credits`, `required_credits`, `gpa`, `conduct_score`, `specialization` và `campus`. Response không trả `password` hoặc `token`.

## Dữ liệu FAQ

150 bản ghi kiến thức có câu hỏi chính, từ khóa và 300 cách hỏi đánh giá. Không xem nội dung mẫu là thông tin chính thức của UTH cho tới khi được người phụ trách xác minh.

## Kiểm thử

```powershell
cd backend
python -m pytest -q
```

Test bao gồm contract BE-01, FAQ, intent, đăng nhập, giới hạn dữ liệu theo tài khoản, chat cá nhân, note/reminder, xác nhận và reminder đến hạn.
