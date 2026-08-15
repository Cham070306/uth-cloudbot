# UTH CloudBot - Phân công giai đoạn Hybrid AI và Cloud

## 1. Mục tiêu giai đoạn

Hoàn thiện UTH CloudBot theo mô hình hybrid:

- Rule-based và dữ liệu FAQ xử lý câu hỏi UTH có nội dung xác định.
- Gemini API chỉ xử lý câu hỏi kiến thức mở hoặc câu hỏi không khớp FAQ.
- Khi Gemini không khả dụng, hệ thống trả fallback an toàn và vẫn dùng được các chức năng rule-based.
- Backend được triển khai bằng Render Free; Firestore Spark được dùng cho dữ liệu cloud.
- Dữ liệu và tài khoản hiện tại chỉ phục vụ demo, không phải dữ liệu chính thức của UTH.

## 2. Trạng thái hiện tại được kiểm tra

Mốc bàn giao chức năng: `e3566df feat: complete FE-02 BE-02 DB-01 handover`.

Mốc Cloud/DevOps mới nhất đã kiểm tra: `f41e9da chore: add Dockerfile and gunicorn for Cloud Run`.

Đã có:

- FE-02: giao diện responsive, gọi API, loading, timeout, retry, feedback, đăng nhập demo và dữ liệu cá nhân.
- BE-02: Flask API, Intent Router, FAQ, lịch học, bài tập, kỳ thi, thông báo, note/reminder và API cá nhân.
- DB-01: local repository, Firestore adapter, schema, seed script, 30 FAQ và 10 tài liệu mẫu.
- Bộ kiểm thử backend; Nghĩa đã tạo lại `.venv` và báo cáo chạy đạt 56 tests.
- Gunicorn đã được thêm vào `backend/requirements.txt`.
- `backend/Dockerfile` và `backend/.dockerignore` đã có trong commit `f41e9da`.
- Remote `origin/feature/cl-01-cloud-run` đã trỏ tới commit `f41e9da`.

Cần hoàn thành/đồng bộ tiếp:

- `develop` local đang ở `f41e9da` và đi trước `origin/develop` một commit; nhóm cần dùng PR từ `feature/cl-01-cloud-run` vào `develop` hoặc đồng bộ theo quy trình đã thống nhất, không coi bản local là đã tích hợp trên GitHub.
- Cần lưu log `56 passed` trong PR hoặc tài liệu evidence để các thành viên khác xác minh.
- Dockerfile hiện bind cố định cổng `8080`; trước khi chạy trên Render cần đổi lệnh Gunicorn để đọc biến `PORT` do nền tảng cung cấp hoặc cấu hình Render dùng đúng cổng này.
- Chưa có Gemini service, `render.yaml`, CI, smoke test cloud, URL deploy hoặc Firestore cloud đã seed.

## 3. API contract phải thống nhất trước khi làm song song

Response `/api/chat` giữ các trường hiện có và bổ sung:

```json
{
  "answer": "Nội dung trả lời",
  "intent": "knowledge",
  "source": {
    "type": "gemini",
    "title": "Gemini AI",
    "url": null
  },
  "ai_generated": true,
  "fallback_used": false,
  "latency_ms": 500
}
```

Quy tắc ưu tiên xử lý:

1. Dữ liệu cá nhân demo.
2. FAQ và dữ liệu rule-based.
3. Gemini cho `knowledge` hoặc `unknown` khi không khớp FAQ.
4. Fallback khi Gemini bị tắt, timeout, hết quota hoặc trả lỗi.

Không tự ý đổi tên trường response sau khi ba thành viên đã thống nhất.

## 4. Phân công Thành viên 1 - Huy (Frontend và UX)

### Mã công việc

- `FE-03`: Hiển thị nguồn trả lời hybrid.
- `FE-04`: Tích hợp URL cloud và kiểm thử responsive.

### Yêu cầu cụ thể

1. Hiển thị rõ nguồn `FAQ`, `Dữ liệu demo`, `Gemini AI` hoặc `Fallback`.
2. Với nội dung Gemini, hiển thị ghi chú: "Nội dung do AI tạo, chỉ dùng để tham khảo."
3. Giữ loading, timeout, retry và câu hỏi gốc khi gọi Gemini mất nhiều thời gian.
4. Hỗ trợ cấu hình API URL cho cả local và Render; không để URL cloud rải rác trong nhiều file.
5. Kiểm tra các luồng FAQ, Gemini, fallback, đăng nhập demo, dữ liệu cá nhân và feedback.
6. Chụp minh chứng giao diện desktop và mobile.

### Thư mục/file đảm nhận chính

- `frontend/public/index.html`
- `frontend/src/js/script.js`
- `frontend/src/css/style.css`
- `frontend/tests/`
- `frontend/README.md`
- `docs/evidence/ui/`

### Không tự sửa

- Logic trong `backend/services/`.
- Firestore adapter.
- Docker, Render và CI.
- API contract khi chưa thống nhất với Châm và Nghĩa.

### Tiêu chí hoàn thành

- Phân biệt đúng FAQ/Gemini/fallback trên giao diện.
- Kết nối được URL Render.
- Desktop và mobile hoạt động; loading/retry không lỗi.
- Có checklist test và ảnh minh chứng.

## 5. Phân công Thành viên 2 - Châm (Backend, dữ liệu và Gemini)

### Mã công việc

- `AI-01`: Tích hợp Gemini API.
- `AI-02`: Timeout, fallback và kiểm thử Gemini.
- `BE-03`: Hoàn thiện API/dữ liệu phục vụ tích hợp.

### Yêu cầu cụ thể

1. Thêm SDK `google-genai` vào `backend/requirements.txt`.
2. Tạo `gemini_service.py`; đọc cấu hình từ biến môi trường.
3. Bổ sung các biến `GEMINI_ENABLED`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_TIMEOUT_SECONDS`.
4. Chỉnh `chat_service.py` theo đúng thứ tự ưu tiên hybrid.
5. Không gửi dữ liệu cá nhân hoặc câu hỏi FAQ đã khớp sang Gemini.
6. Bắt lỗi thiếu key, key sai, timeout, HTTP 429, lỗi mạng và response rỗng.
7. Gemini lỗi không được làm `/api/chat` trả HTTP 500; phải dùng fallback.
8. Viết test bằng mock; unit test không gọi Gemini thật.
9. Bổ sung `GET /api/documents` hoặc cập nhật tài liệu nếu nhóm quyết định không dùng endpoint này.
10. Thống nhất `/api/schedules` và `/api/me/schedule` với Huy.
11. Hỗ trợ Nghĩa cấu hình Firestore credential trên Render và chạy seed.
12. Cập nhật Postman, API docs, backend README và `.env.example`.

### Thư mục/file đảm nhận chính

- `backend/app.py`
- `backend/config.py`
- `backend/routes/`
- `backend/services/`
- `backend/repositories/`
- `backend/models/`
- `backend/tests/`
- `backend/requirements.txt`
- `backend/postman/`
- `backend/README.md`
- `data/sample/`
- `data/schemas/`
- `backend/scripts/seed_data.py`
- `docs/api/`
- `docs/architecture/`

### Không tự sửa

- Giao diện frontend, trừ khi có thống nhất với Huy.
- `render.yaml`, CI hoặc smoke test cloud, trừ phần review backend.

### Tiêu chí hoàn thành

- Toàn bộ test cũ và test Gemini đạt.
- FAQ luôn được ưu tiên hơn Gemini.
- Gemini hoạt động khi bật và fallback đúng khi lỗi/tắt.
- Response đúng contract đã thống nhất.
- Nghĩa có đủ biến môi trường và hướng dẫn để deploy.

## 6. Phân công Thành viên 3 - Nghĩa (Cloud, DevOps và QA)

### Mã công việc

- `CL-01R`: Triển khai Render Free.
- `CL-02R`: Cấu hình Gemini và môi trường chạy cloud.
- `DB-02`: Tạo Firestore Spark và seed dữ liệu.
- `CI-01`: GitHub Actions.
- `QA-02`: Smoke test và kiểm thử hybrid trên cloud.

### Yêu cầu cụ thể

1. Mở/hoàn thiện PR từ `feature/cl-01-cloud-run` vào `develop`, đính kèm commit `f41e9da` và log 56 tests; không push trực tiếp để thay quy trình review.
2. Điều chỉnh Docker/Gunicorn để đọc cổng `PORT` của Render, sau đó build Docker local, chạy với `DATA_BACKEND=local` và kiểm tra health/chat/login.
3. Tạo `render.yaml` và Render Free Web Service; cấu hình Gunicorn, biến `PORT` và health check `/api/health`.
4. Deploy trước với `DATA_BACKEND=local`, `GEMINI_ENABLED=false` để tách lỗi deploy khỏi lỗi dịch vụ ngoài.
5. Sau khi Châm merge AI-01, cấu hình Gemini API key bằng Render Environment Secret và bật Gemini.
6. Tạo Firestore Spark, phối hợp Châm cấu hình credential và chạy seed tối thiểu 30 FAQ, 10 documents.
7. Chạy seed lần hai để xác nhận không sinh dữ liệu trùng.
8. Chuyển sang `DATA_BACKEND=firestore`; kiểm tra conversation và feedback còn sau restart.
9. Tạo GitHub Actions chạy pytest với `DATA_BACKEND=local`; CI không gọi Gemini thật hoặc yêu cầu Firestore credential.
10. Tạo smoke test nhận `BASE_URL` và kiểm tra health, FAQ, Gemini, fallback, login, API cá nhân và feedback.
11. Lưu URL, log, ảnh và test report; viết hướng dẫn deploy/rollback và known issues.
12. Bàn giao URL Render và cấu hình CORS cho Huy.

### Thư mục/file đảm nhận chính

- `backend/Dockerfile`
- `backend/.dockerignore`
- `render.yaml`
- `.github/workflows/`
- `tests/integration/`
- `infra/render/`
- `docs/deployment/`
- `docs/evidence/cloud/`
- `docs/handover/`

Nghĩa chỉ phối hợp/review, không tự thay đổi logic trong `backend/services/chat_service.py` hoặc API contract.

### Tiêu chí hoàn thành

- PR Cloud/DevOps được review/merge vào `origin/develop` và có log test đạt.
- Docker build/chạy local thành công.
- Có URL Render HTTPS; health và chat hoạt động.
- Gemini hoạt động và fallback được kiểm chứng.
- Firestore đã seed và đọc/ghi thành công.
- CI đạt; có smoke test, test report, log và tài liệu rollback.

## 7. Công việc chung

1. Chốt API contract trước khi phát triển song song.
2. Review PR chéo: Huy review response hiển thị, Châm review cấu hình backend, Nghĩa review khả năng build/deploy/test.
3. Không sử dụng dữ liệu sinh viên thật; ghi rõ dữ liệu demo trong giao diện và báo cáo.
4. Repository public không được chứa API key hoặc credential; `.env.example` chỉ ghi tên biến và giá trị minh họa.
5. Chuẩn bị kịch bản demo: FAQ có dấu, FAQ không dấu, dữ liệu cá nhân, Gemini, fallback, feedback và minh chứng cloud.
6. Chuẩn bị chế độ local/MOCK nếu Internet, Render hoặc Gemini gặp sự cố.

## 8. Thứ tự tích hợp và merge

Ba nhánh có thể làm song song:

- Châm: `feature/ai-01-gemini`.
- Huy: `feature/fe-03-ai-source`.
- Nghĩa: tiếp tục `feature/cl-01-cloud-run` hoặc tạo `feature/cl-01-render` sau khi thống nhất với nhóm.

Thứ tự tích hợp:

1. Nghĩa mở/hoàn thiện PR cho commit `f41e9da`, bổ sung log test và đưa thay đổi Docker/Gunicorn vào `origin/develop` sau review.
2. Châm merge Gemini service, fallback và API contract vào `develop`.
3. Huy cập nhật từ `develop`, kiểm tra response thật và merge frontend.
4. Nghĩa cập nhật từ `develop`, deploy/redeploy Render và cấu hình Gemini.
5. Châm và Nghĩa hoàn thiện Firestore Spark.
6. Nghĩa chạy QA tổng thể; Huy/Châm sửa lỗi theo phạm vi.
7. Cả nhóm chốt release, báo cáo, slide và kịch bản demo.

## 9. Sửa đổi quy trình so với kế hoạch ban đầu

Quy trình mới thay đổi từ mô hình phụ thuộc Cloud Run sang triển khai tăng dần nhằm tránh blocker Billing và giảm rủi ro tích hợp. Backend được kiểm thử và deploy lên Render trước bằng local repository, không bật Gemini; sau khi URL cơ bản hoạt động mới lần lượt bật Gemini và Firestore. Rule-based trở thành nguồn trả lời ưu tiên cho FAQ/dữ liệu UTH, còn Gemini chỉ là tầng bổ sung cho kiến thức mở và luôn có fallback. Ba thành viên làm song song trên các nhánh và vùng file riêng, sau đó tích hợp theo thứ tự backend contract - frontend - cloud - database - QA. Cloud Run, Cloud Storage, Secret Manager và đăng nhập production được chuyển thành hướng mở rộng; đầu ra MVP tập trung vào URL Render, Firestore Spark, Gemini free tier, CI, test report và bản demo dự phòng.

## 10. Điều kiện hoàn thành giai đoạn

- Tất cả test local và CI đạt.
- URL Render hoạt động qua HTTPS.
- FAQ rule-based, Gemini và fallback đều có test minh chứng.
- Firestore chứa dữ liệu seed và lưu được conversation/feedback.
- Frontend hoạt động trên desktop/mobile với URL cloud.
- Không có lỗi P0; lỗi còn lại được ghi trong known issues.
- Có deployment runbook, rollback, test report, ảnh/log và phương án demo offline.
