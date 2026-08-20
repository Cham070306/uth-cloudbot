/**
 * ============================================================
 *  CẤU HÌNH KẾT NỐI BACKEND — CHỈ SỬA TRONG FILE NÀY
 * ============================================================
 * Đây là NƠI DUY NHẤT chứa URL backend — không rải URL ở file khác.
 */

const CONFIG = {
  // Đổi ENV để chuyển giữa local và Render — không sửa URL ở đâu khác.
  // "local"  -> dùng LOCAL_URL
  // "render" -> dùng RENDER_URL
  ENV: "render",

  LOCAL_URL: "http://localhost:8080",
  RENDER_URL: "https://uth-cloudbot.onrender.com",

  get API_BASE_URL() {
    return this.ENV === "local" ? this.LOCAL_URL : this.RENDER_URL;
  },

  // Đã tắt mock — gọi thẳng backend thật.
  // Đổi lại true để test giao diện bằng dữ liệu giả khi backend down.
  USE_MOCK: false,

  ENDPOINTS: {
    health: "/api/health",
    chat: "/api/chat",
    feedback: "/api/feedback",
  },

  // Backend thật dùng "message" (đã Châm xác nhận qua Postman).
  REQUEST_FIELDS: {
    question: "message",
  },

  // "answer" đã xác nhận. "source"/"updated_at"/"source_type" CHƯA xác nhận —
  // nếu backend trả tên khác, chỉ sửa giá trị bên phải ở đây.
  RESPONSE_FIELDS: {
    answer: "answer",
    source: "source",
    sourceType: "source_type", // kỳ vọng backend trả: "faq" | "demo" | "gemini" | "fallback"
    updatedAt: "updated_at",
  },

  FEEDBACK_FIELDS: {
    question: "message",
    answer: "answer",
    rating: "rating",
  },

  // Thời gian chờ Gemini có thể lâu hơn FAQ thường -> để timeout rộng hơn.
  REQUEST_TIMEOUT_MS: 20000,

  // Nhãn hiển thị + ghi chú theo từng loại nguồn.
  SOURCE_LABELS: {
    faq: { label: "FAQ", note: null },
    demo: { label: "Dữ liệu demo", note: null },
    gemini: { label: "Gemini AI", note: "Nội dung do AI tạo, chỉ dùng để tham khảo." },
    fallback: { label: "Fallback", note: null },
  },
};

/**
 * Suy luận loại nguồn khi backend không trả field "source_type" riêng,
 * dựa trên nội dung chuỗi "source" (dự phòng, ưu tiên field source_type nếu có).
 */
function inferSourceType(rawSourceType, rawSourceText) {
  if (rawSourceType && CONFIG.SOURCE_LABELS[rawSourceType]) {
    return rawSourceType;
  }
  const text = (rawSourceText || "").toLowerCase();
  if (text.includes("gemini") || text.includes("ai")) return "gemini";
  if (text.includes("faq")) return "faq";
  if (text.includes("demo") || text.includes("mẫu")) return "demo";
  return "fallback";
}
