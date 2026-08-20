/**
 * ============================================================
 *  CẤU HÌNH KẾT NỐI BACKEND — CHỈ SỬA TRONG FILE NÀY
 * ============================================================
 * Nếu backend thật (Flask/Cloud Run của Châm & Nghĩa) dùng tên
 * field khác, CHỈ CẦN sửa ở đây — không cần đụng vào script.js.
 */

const CONFIG = {
  // URL backend thật (Render).
  API_BASE_URL: "https://uth-cloudbot.onrender.com",

  // Đã tắt mock — app sẽ gọi thẳng backend thật ở trên.
  // Nếu backend lỗi/chưa sẵn sàng, tạm đổi lại thành true để test giao diện bằng dữ liệu giả.
  USE_MOCK: false,

  ENDPOINTS: {
    health: "/api/health",
    chat: "/api/chat",
    feedback: "/api/feedback",
  },

  // Tên field gửi lên server khi hỏi — backend thật dùng "message"
  REQUEST_FIELDS: {
    question: "message",
  },

  // Tên field nhận lại từ server. "answer" đã được Châm xác nhận.
  // "source" và "updated_at" CHƯA được xác nhận — nếu backend không trả
  // 2 field này (hoặc đặt tên khác), sửa lại giá trị bên phải cho khớp.
  RESPONSE_FIELDS: {
    answer: "answer",
    source: "source",
    updatedAt: "updated_at",
    intent: "intent",
  },

  // Field gửi lên khi bấm feedback 👍/👎
  // CHƯA được Châm xác nhận endpoint /api/feedback có tồn tại hay dùng
  // tên field gì — đang đoán theo cùng quy ước với /api/chat ("message").
  FEEDBACK_FIELDS: {
    question: "message",
    answer: "answer",
    rating: "rating", // giá trị gửi: "up" hoặc "down"
  },

  REQUEST_TIMEOUT_MS: 10000,
};
