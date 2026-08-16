import logging

from config import Config


logger = logging.getLogger(__name__)
MODEL_ID = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = """Bạn là trợ lý kiến thức chung và học tập của UTH CloudBot.
Chỉ trả lời kiến thức chung hoặc hỗ trợ học tập bằng tiếng Việt, rõ ràng và ngắn gọn.
Trình bày dễ đọc bằng Markdown đơn giản: đoạn văn ngắn, tiêu đề khi cần, danh sách cho
các ý song song và khối mã cho ví dụ lập trình. Không dùng bảng Markdown hoặc HTML.
Không tự tạo hoặc khẳng định học phí, lịch học, lịch thi, quy định, thông báo hay thông tin
chính thức của Trường Đại học Giao thông vận tải TP.HCM (UTH). Nếu người dùng hỏi những
nội dung đó, hãy nói rằng bạn không có nguồn chính thức và hướng dẫn họ kiểm tra kênh UTH.
Không yêu cầu hoặc suy đoán dữ liệu cá nhân của sinh viên."""


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
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
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
