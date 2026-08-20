# Checklist test thủ công — Frontend UTH CloudBot

Test trên **desktop trước**, sau đó lặp lại trên **mobile** (thu nhỏ trình duyệt hoặc mở bằng điện thoại). Với mỗi dòng, đánh dấu ✅ và chụp ảnh minh chứng lưu vào `docs/evidence/ui/`.

| # | Luồng test | Cách test | Kết quả mong đợi |
|---|---|---|---|
| 1 | FAQ | Hỏi "học phí học kỳ này" | Trả lời đúng, badge nguồn hiện "FAQ" |
| 2 | Dữ liệu demo | Hỏi câu liên quan lịch học mẫu | Badge hiện "Dữ liệu demo" |
| 3 | Gemini AI | Hỏi câu kiến thức chung không có trong FAQ | Badge "Gemini AI" + hiện ghi chú "Nội dung do AI tạo, chỉ dùng để tham khảo." |
| 4 | Fallback | Hỏi câu vô nghĩa/không rõ nghĩa | Badge "Fallback", trả lời hướng dẫn hỏi lại |
| 5 | Loading | Gửi bất kỳ câu hỏi nào | Thấy 3 chấm nhảy trong lúc chờ |
| 6 | Timeout / lỗi mạng | Tắt wifi rồi gửi câu hỏi | Hiện banner lỗi + nút "Thử lại", câu hỏi gốc không bị mất |
| 7 | Retry giữ câu hỏi gốc | Bấm "Thử lại" sau lỗi | Gửi lại đúng câu hỏi cũ, không cần gõ lại |
| 8 | Feedback | Bấm 👍 hoặc 👎 dưới câu trả lời | Nút disabled, hiện dòng cảm ơn |
| 9 | Responsive desktop | Mở trên màn hình máy tính | Bố cục rộng, đọc thoải mái |
| 10 | Responsive mobile | Thu nhỏ trình duyệt còn ~375px hoặc mở bằng điện thoại | Bố cục co giãn đúng, không bị tràn ngang |

## Ghi chú
- Đăng nhập demo và dữ liệu cá nhân: cập nhật thêm khi backend cung cấp route đăng nhập (hiện `config.js` mới chỉ có `/api/chat`, `/api/health`, `/api/feedback`).
- Ảnh chụp minh chứng: đặt tên file theo mẫu `01-faq-desktop.png`, `01-faq-mobile.png`... để dễ đối chiếu với bảng trên.
