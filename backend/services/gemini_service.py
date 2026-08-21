import logging
import re

from config import Config


logger = logging.getLogger(__name__)
MODEL_ID = "gemini-3.5-flash"
GEMINI_MAX_OUTPUT_TOKENS = 380

SYSTEM_INSTRUCTION = """Bạn là UTH CloudBot, trợ lý kiến thức chung và học tập cho sinh viên.

QUY TẮC TRẢ LỜI
1. Luôn trả lời bằng tiếng Việt tự nhiên, thân thiện và đi thẳng vào câu hỏi. Không chào hỏi
   dài dòng, không lặp lại nguyên văn câu hỏi và không nói về các quy tắc này.
2. Mở đầu bằng câu trả lời trực tiếp trong 1-2 câu ngắn. Sau phần mở đầu phải xuống dòng.
   Nếu có nhiều ý, chỉ chọn tối đa 5 ý quan trọng nhất; mỗi ý nằm trên một dòng và bắt đầu
   bằng dấu "•". Không tạo danh sách lồng nhau và không viết tiêu đề đánh số như "1. Nhóm...".
3. Ưu tiên câu trả lời từ 60-130 từ; câu đơn giản có thể ngắn hơn. Mỗi đoạn tối đa 3 câu.
   Không dùng bảng, HTML,
   tiêu đề Markdown, dấu ** hoặc ký hiệu định dạng mà giao diện có thể hiển thị thô.
4. Với hướng dẫn thao tác, chỉ dùng tối đa 4 bước rõ ràng bằng "1.", "2.", "3.". Mỗi bước
   bắt đầu ở một dòng mới. Với nội dung
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


def _to_plain_text(value):
    """Remove Markdown tokens when a model ignores the plain-text instruction."""
    value = re.sub(r"```(?:[a-zA-Z0-9_+-]+)?\s*", "", value)
    value = value.replace("```", "").replace("`", "")
    value = re.sub(r"^\s{0,3}#{1,6}\s*", "", value, flags=re.MULTILINE)
    value = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda match: match.group(1) or match.group(2), value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", value)
    value = re.sub(r"^\s*[-*+]\s+", "• ", value, flags=re.MULTILINE)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def generate_answer(message: str) -> dict:
    if not Config.GEMINI_ENABLED:
        _unavailable("disabled")
    if not Config.GEMINI_API_KEY:
        _unavailable("missing_api_key")
    if not Config.GEMINI_MODEL:
        _unavailable("invalid_model")

    try:
        client = _create_client(Config.GEMINI_API_KEY, Config.GEMINI_TIMEOUT_SECONDS)
        response = _generate(client, Config.GEMINI_MODEL, message)
        answer = _to_plain_text(getattr(response, "text", None) or "")
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
