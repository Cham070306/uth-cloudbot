/**
 * ============================================================
 *  CẤU HÌNH KẾT NỐI BACKEND — CHỈ SỬA TRONG FILE NÀY
 * ============================================================
 * Đã đối chiếu trực tiếp với code thật (backend/routes/chat.py,
 * feedback.py, auth.py, services/chat_service.py, gemini_service.py,
 * faq_service.py, mock_chat_service.py) — không còn đoán.
 */

const CONFIG = {
  ENV: "render",
  LOCAL_URL: "http://localhost:8080",
  RENDER_URL: "https://uth-cloudbot.onrender.com",

  get API_BASE_URL() {
    return this.ENV === "local" ? this.LOCAL_URL : this.RENDER_URL;
  },

  USE_MOCK: false,

  ENDPOINTS: {
    health: "/api/health",
    chat: "/api/chat",
    feedback: "/api/feedback",
    login: "/api/auth/login", // đăng nhập thật, trả về access_token
  },

  // Backend chấp nhận cả "message" và "question" (routes/chat.py) — dùng "message".
  REQUEST_FIELDS: {
    question: "message",
  },

  // Field top-level thật từ services/chat_service.py — "source" LÀ MỘT OBJECT:
  // { type, title, url }, không phải chuỗi. answer/intent/updated_at là chuỗi/None.
  // Có sẵn 2 cờ boolean đáng tin cậy: ai_generated, fallback_used.
  RESPONSE_FIELDS: {
    answer: "answer",
    source: "source", // object {type, title, url}
    updatedAt: "updated_at",
    aiGenerated: "ai_generated",
    fallbackUsed: "fallback_used",
  },

  // routes/feedback.py (nhánh "legacy" mà frontend này dùng) yêu cầu đúng:
  // { question: string, answer: string, vote: "up" | "down" }
  FEEDBACK_FIELDS: {
    question: "question",
    answer: "answer",
    vote: "vote", // giá trị: "up" hoặc "down" — KHÔNG phải "rating"
  },

  // Gemini có thể chậm hơn FAQ -> timeout rộng hơn.
  REQUEST_TIMEOUT_MS: 20000,

  // Giá trị source.type THẬT từ backend (đã đọc trực tiếp trong code):
  //   "sample"            -> FAQ thật (services/faq_service.py, build_faq_response)
  //   "mock"              -> Dữ liệu demo (data/mock_responses.json, khi intent
  //                          là schedule/exam_schedule/document — chưa có dữ liệu thật)
  //   "mock_student_data" -> Dữ liệu demo cá nhân (lịch học/bài tập giả lập của sinh viên)
  //   "gemini"            -> Gemini AI (services/gemini_service.py)
  //   "fallback"          -> Fallback (không khớp FAQ, không phải câu hỏi kiến thức)
  //   "system"            -> Thông báo hệ thống (vd: yêu cầu đăng nhập) -> coi như fallback
  SOURCE_LABELS: {
    sample: { label: "FAQ", note: null },
    mock: { label: "Dữ liệu demo", note: null },
    mock_student_data: { label: "Dữ liệu demo", note: null },
    gemini: { label: "Gemini AI", note: "Nội dung do AI tạo, chỉ dùng để tham khảo." },
    fallback: { label: "Fallback", note: null },
    system: { label: "Fallback", note: null },
  },
};

/**
 * Suy ra loại nguồn để chọn badge hiển thị — ưu tiên theo thứ tự:
 * 1) 2 cờ boolean đáng tin cậy nhất (ai_generated / fallback_used)
 * 2) source.type thật từ backend
 * 3) fallback an toàn nếu gặp giá trị lạ chưa biết
 */
function inferSourceType(sourceObj, aiGenerated, fallbackUsed) {
  if (aiGenerated) return "gemini";
  if (fallbackUsed) return "fallback";
  const type = sourceObj && sourceObj.type;
  if (type && CONFIG.SOURCE_LABELS[type]) return type;
  return "fallback";
}

/** source là object {type, title, url} — ghép thành chuỗi hiển thị gọn cho người dùng. */
function formatSourceText(sourceObj) {
  if (!sourceObj || typeof sourceObj !== "object") return "Không rõ nguồn";
  return sourceObj.title || sourceObj.type || "Không rõ nguồn";
}
