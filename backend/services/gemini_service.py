import logging

from config import Config


logger = logging.getLogger(__name__)
MODEL_ID = "gemini-3.5-flash"
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_OUTPUT_TOKENS = 500

SYSTEM_INSTRUCTION = """Bạn là UTH CloudBot, trợ lý kiến thức chung và học tập cho sinh viên.

QUY TẮC TRẢ LỜI
1. Luôn trả lời bằng tiếng Việt tự nhiên, thân thiện và đi thẳng vào câu hỏi. Không chào hỏi
   dài dòng, không lặp lại nguyên văn câu hỏi và không nói về các quy tắc này.
2. Mở đầu bằng câu trả lời trực tiếp trong 1-2 câu. Nếu có từ hai ý trở lên, xuống dòng và
   dùng dấu "•" cho từng ý. Chỉ đưa ví dụ khi ví dụ thực sự giúp người dùng hiểu hoặc làm được.
3. Ưu tiên câu trả lời từ 80-180 từ; câu đơn giản có thể ngắn hơn. Không dùng bảng, HTML,
   tiêu đề Markdown, dấu ** hoặc ký hiệu định dạng mà giao diện có thể hiển thị thô.
4. Với hướng dẫn thao tác, trình bày theo thứ tự rõ ràng bằng "1.", "2.", "3.". Với nội dung
   kỹ thuật, giải thích thuật ngữ lần đầu và đặt đoạn mã trong khối riêng nếu cần.
5. Không bịa nguồn, con số, ngày tháng hoặc quy định. Nếu chưa chắc, nói ngắn gọn giới hạn
   của câu trả lời và đề nghị người dùng kiểm tra nguồn đáng tin cậy.

GIỚI HẠN UTH VÀ DỮ LIỆU CÁ NHÂN
• Không tự tạo hoặc khẳng định học phí, lịch học, lịch thi, phòng thi, quy định, thông báo hay
  thông tin chính thức của Trường Đại học Giao thông vận tải TP.HCM (UTH).
• Nếu câu hỏi cần thông tin chính thức của UTH, nói rõ bạn chưa có nguồn xác thực và hướng
  dẫn kiểm tra cổng sinh viên hoặc kênh chính thức của trường.
• Không yêu cầu, suy đoán hoặc tiết lộ dữ liệu cá nhân của sinh viên.

KẾT THÚC
Chỉ thêm một câu gợi ý tiếp theo khi nó hữu ích và liên quan trực tiếp. Không kết thúc mọi
câu trả lời bằng một câu hỏi xã giao."""


class GeminiUnavailableError(RuntimeError):
    """Gemini cannot provide a safe answer and the caller should use fallback."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def _unavailable(reason):
    logger.warning("Gemini unavailable: %s", reason)
    raise GeminiUnavailableError(reason)


def _create_client(api_key, timeout_seconds):
    # Imported lazily so rule-based mode works without loading the external SDK.
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout_seconds * 1000),
    )


def _generate(client, model, message):
    from google.genai import types

    return client.models.generate_content(
        model=model,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=GEMINI_TEMPERATURE,
            max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
        ),
    )


def _error_reason(error):
    status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
    details = f"{type(error).__name__} {error}".lower()
    if status_code == 429 or "429" in details or "resource_exhausted" in details or "quota" in details:
        return "quota_exceeded"
    if status_code in {401, 403} or "unauthenticated" in details or "permission_denied" in details:
        return "authentication_error"
    if status_code == 404 or (
        "model" in details and any(term in details for term in ("invalid", "not found", "unsupported"))
    ):
        return "invalid_model"
    if any(term in details for term in ("timeout", "timed out", "deadline_exceeded", "deadline exceeded")):
        return "timeout"
    if any(term in details for term in ("connect", "network", "dns", "socket")):
        return "network_error"
    return "unexpected_error"


def generate_answer(message: str) -> dict:
    if not Config.GEMINI_ENABLED:
        _unavailable("disabled")
    if not Config.GEMINI_API_KEY:
        _unavailable("missing_api_key")
    if Config.GEMINI_MODEL != MODEL_ID:
        _unavailable("invalid_model")

    try:
        client = _create_client(Config.GEMINI_API_KEY, Config.GEMINI_TIMEOUT_SECONDS)
        response = _generate(client, Config.GEMINI_MODEL, message)
        answer = (getattr(response, "text", None) or "").strip()
        if not answer:
            _unavailable("empty_response")
    except GeminiUnavailableError:
        raise
    except Exception as error:
        reason = _error_reason(error)
        logger.warning("Gemini unavailable: %s", reason)
        raise GeminiUnavailableError(reason) from error

    return {
        "answer": answer,
        "source": {"type": "gemini", "title": "Gemini AI", "url": None},
        "ai_generated": True,
        "fallback_used": False,
    }
