import logging

from config import Config


logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """Bạn là trợ lý kiến thức chung và học tập của UTH CloudBot.
Chỉ trả lời kiến thức chung hoặc hỗ trợ học tập bằng tiếng Việt, rõ ràng và ngắn gọn.
Không tự tạo hoặc khẳng định học phí, lịch học, lịch thi, quy định, thông báo hay thông tin
chính thức của Trường Đại học Giao thông vận tải TP.HCM (UTH). Nếu người dùng hỏi những
nội dung đó, hãy nói rằng bạn không có nguồn chính thức và hướng dẫn họ kiểm tra kênh UTH.
Không yêu cầu hoặc suy đoán dữ liệu cá nhân của sinh viên."""


class GeminiUnavailableError(RuntimeError):
    """Gemini cannot provide a safe answer and the caller should use fallback."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


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
        return "invalid_api_key"
    if "timeout" in details or "timed out" in details:
        return "timeout"
    if any(term in details for term in ("connect", "network", "dns", "socket")):
        return "network_error"
    return "unexpected_error"


def generate_answer(message: str) -> dict:
    if not Config.GEMINI_ENABLED:
        raise GeminiUnavailableError("disabled")
    if not Config.GEMINI_API_KEY:
        raise GeminiUnavailableError("missing_api_key")
    if not Config.GEMINI_MODEL:
        raise GeminiUnavailableError("missing_model")

    try:
        client = _create_client(Config.GEMINI_API_KEY, Config.GEMINI_TIMEOUT_SECONDS)
        response = _generate(client, Config.GEMINI_MODEL, message)
        answer = (getattr(response, "text", None) or "").strip()
        if not answer:
            raise GeminiUnavailableError("empty_response")
    except GeminiUnavailableError:
        raise
    except Exception as error:
        reason = _error_reason(error)
        logger.warning("Gemini request unavailable: %s", reason)
        raise GeminiUnavailableError(reason) from error

    return {
        "answer": answer,
        "source": {"type": "gemini", "title": "Gemini AI", "url": None},
        "ai_generated": True,
        "fallback_used": False,
    }
