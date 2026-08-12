# DB-01 — thiết kế dữ liệu UTH CloudBot

Tất cả dữ liệu mẫu là demo, không phải dữ liệu UTH đã kiểm chứng. Document ID dùng chuỗi ổn định; thời gian dùng ISO-8601 hoặc Firestore Timestamp.

| Collection | ID | Trường bắt buộc | Index dự kiến |
|---|---|---|---|
| `faqs` | `faq-*` | `question:string`, `keywords:array`, `answer:string`, `source:map`, `updated_at` | search index khi mở rộng |
| `schedules` | `schedule-*` | `student_id`, `course_code`, `course_name`, `date`, `start_time`, `end_time` | `(student_id,date,start_time)` |
| `documents` | `doc-*` | `title`, `category`, `updated_at`; `url:string|null` | `(category,updated_at desc)` |
| `conversations` | `msg-*` | `question`, `answer`, `intent`, `created_at`; `student_id:string|null` | `(student_id,created_at desc)` |
| `feedback` | `feedback-*` | `helpful:boolean`, `created_at`; `message_id:string|null` | `message_id`, `created_at desc` |
| `students` | mã demo | `username`, `password`, `token`, `full_name` | unique username/token (demo) |
| `assignments` | `assignment-*` | `student_id`, `course_code`, `title`, `due_at`, `status` | `(student_id,status,due_at)` |
| `exams` | `exam-*` | `student_id`, `course_code`, `title`, `start_at`, `end_at` | `(student_id,start_at)` |
| `announcements` | `announcement-*` | `student_id`, `title`, `published_at`, `read` | `(student_id,read,published_at desc)` |
| `notes` | `note-*` | `student_id`, `content`, `status`, `created_at` | `(student_id,created_at desc)` |
| `reminders` | `reminder-*` | `student_id`, `content`, `remind_at`, `status` | `(student_id,status,remind_at)` |

`DataRepository` định nghĩa `list/get/upsert/clear_runtime`. `LocalRepository` là mặc định và nạp JSON demo; runtime records sống trong bộ nhớ. `FirestoreRepository` dùng cùng interface, import SDK muộn và chỉ yêu cầu Application Default Credentials khi `DATA_BACKEND=firestore`.
