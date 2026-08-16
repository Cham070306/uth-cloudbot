# DB-01 — thiết kế dữ liệu UTH CloudBot

Tất cả dữ liệu mẫu là demo, không phải dữ liệu UTH đã kiểm chứng. Document ID dùng chuỗi ổn định; thời gian dùng ISO-8601 hoặc Firestore Timestamp.

Yêu cầu tối thiểu của giai đoạn ban đầu là 30 FAQ demo. Hiện repository triển khai 150 FAQ demo và dataset đánh giá có 300 cách hỏi tại `data/evaluation/faq_questions.json`.

Dataset trợ lý cá nhân hiện có 10 hồ sơ, 60 lịch học, 35 bài tập, 20 kỳ thi, 30 thông báo và 30 tài liệu. Toàn bộ hồ sơ, lịch học, bài tập, kỳ thi và thông báo là dữ liệu demo, không phải dữ liệu sinh viên UTH thật. Học kỳ minh họa `2026-1` kéo dài từ `2026-08-17` đến `2026-12-20`, múi giờ `Asia/Ho_Chi_Minh`.

| Collection | ID | Trường bắt buộc | Index dự kiến |
|---|---|---|---|
| `faqs` | `faq-*` | `question:string`, `keywords:array`, `answer:string`, `source:map`, `updated_at` | search index khi mở rộng |
| `schedules` | `schedule-*` | `student_id`, `course_code`, `course_name`, `date`, `start_time`, `end_time` | `(student_id,date,start_time)` |
| `documents` | `doc-*` | `title`, `category`, `updated_at`; `url:string|null` | `(category,updated_at desc)` |
| `conversations` | `msg-*` | `question`, `answer`, `intent`, `created_at`; `student_id:string|null` | `(student_id,created_at desc)` |
| `feedback` | `feedback-*` | `helpful:boolean`, `created_at`; `message_id:string|null` | `message_id`, `created_at desc` |
| `students` | mã demo | `username`, `password`, `token`, `full_name`, `email`, `class_code`, `major`, `semester`, `timezone`; hồ sơ demo mở rộng gồm khoa, khóa, tín chỉ, GPA và rèn luyện | unique username/token (demo) |
| `assignments` | `assignment-*` | `student_id`, `course_code`, `title`, `due_at`, `status` | `(student_id,status,due_at)` |
| `exams` | `exam-*` | `student_id`, `course_code`, `title`, `start_at`, `end_at` | `(student_id,start_at)` |
| `announcements` | `announcement-*` | `student_id`, `title`, `published_at`, `read` | `(student_id,read,published_at desc)` |
| `notes` | `note-*` | `student_id`, `content`, `status`, `created_at` | `(student_id,created_at desc)` |
| `reminders` | `reminder-*` | `student_id`, `content`, `remind_at`, `status` | `(student_id,status,remind_at)` |

`DataRepository` định nghĩa `list/get/upsert/clear_runtime`. `LocalRepository` là mặc định và nạp JSON demo; runtime records sống trong bộ nhớ. `FirestoreRepository` dùng cùng interface, import SDK muộn và chỉ yêu cầu Application Default Credentials khi `DATA_BACKEND=firestore`.
