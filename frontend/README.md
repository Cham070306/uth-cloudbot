# UTH CloudBot — FE-02 tích hợp API

FE-02 giữ nguyên giao diện chatbot hiện có và kết nối mặc định tới backend BE-01 tại `http://localhost:8080`. Frontend hỗ trợ loading, timeout, retry, chuẩn hóa response thiếu trường, render nội dung an toàn và gửi feedback theo cả contract hiện tại lẫn contract có `message_id` trong tương lai.

Frontend còn kiểm tra health, hỗ trợ đăng nhập demo `sv001` / `demo123`, lưu token trong `sessionStorage`, hiển thị metadata và `data.items`, đồng thời xác nhận/hủy note hoặc reminder. Token và dữ liệu cá nhân chỉ dùng cho demo local.

## Chạy local

Yêu cầu Python 3.11 trở lên. Mở PowerShell thứ nhất tại thư mục `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PORT = "8080"
python app.py
```

Mở PowerShell thứ hai tại thư mục gốc repository và phục vụ frontend ở cổng 5173:

```powershell
python -m http.server 5173 --directory frontend
```

Truy cập `http://localhost:5173/public/`. Không mở `index.html` trực tiếp bằng `file://`, vì origin đó không phù hợp để kiểm tra CORS và tích hợp API.

## Kiểm tra thủ công

1. Gửi một câu hỏi và xác nhận badge `LIVE`, typing indicator xuất hiện, nút gửi/suggestion/history/follow-up bị khóa trong lúc chờ, sau đó câu trả lời và nguồn hiển thị.
2. Dừng backend, gửi câu hỏi và xác nhận có thông báo mất kết nối. Bấm **Thử lại** sau khi chạy lại backend; câu hỏi thất bại phải được gửi lại nguyên vẹn.
3. Để kiểm tra timeout, tạm giảm `TIMEOUT_MS` trong `src/js/script.js` hoặc làm backend phản hồi chậm hơn giới hạn, rồi xác nhận thông báo timeout và nút retry.
4. Chọn 👍 hoặc 👎. Hai nút phải bị khóa khi gửi; chỉ nút được chọn mới đổi trạng thái sau phản hồi HTTP thành công. Khi backend tắt, câu trả lời vẫn còn và xuất hiện thông báo feedback nhẹ.
5. Bấm **Cuộc trò chuyện mới** trong khi bình thường và trong lúc loading; xác nhận thread, lỗi, nguồn, history active và input đều trở về trạng thái ban đầu.
6. Thử gửi nội dung rỗng, chỉ có khoảng trắng và nội dung gần giới hạn 300 ký tự để kiểm tra validation/focus.
7. Đăng nhập tài khoản demo, hỏi lịch cá nhân, bài tập, deadline, kỳ thi và thông báo; đăng xuất rồi hỏi lại để kiểm tra lời nhắc đăng nhập.
8. Yêu cầu ghi chú/nhắc việc, kiểm tra xác nhận và hủy bằng chuột lẫn bàn phím.

## Chuyển LIVE/MOCK

Mở `src/js/script.js` và đổi hằng số:

```js
const USE_MOCK = false; // LIVE, mặc định
const API_BASE = "http://localhost:8080";
```

Đặt `USE_MOCK = true` để dùng dữ liệu minh họa không cần backend. Badge tự đổi giữa `LIVE` và `MOCK`.

## Kiểm tra backend contract

Tại thư mục `backend`, chạy:

```powershell
python -m pytest -q
```

Các request frontend sử dụng là `POST /api/chat` với `{ "message": "..." }` và `POST /api/feedback`. Nếu chat response có `message_id`, feedback gửi `{message_id, helpful}`; nếu chưa có, frontend gửi `{question, answer, vote}`.
