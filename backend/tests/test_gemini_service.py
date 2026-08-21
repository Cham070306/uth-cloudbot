from types import SimpleNamespace

import pytest

from app import create_app
from config import Config, _get_bool, _get_positive_int
from services import chat_service, gemini_service
from services.gemini_service import (
    GEMINI_MAX_OUTPUT_TOKENS,
    SYSTEM_INSTRUCTION,
    GeminiUnavailableError,
    MODEL_ID,
    _to_plain_text,
)


@pytest.fixture(autouse=True)
def gemini_config(disable_real_gemini, monkeypatch):
    monkeypatch.setattr(Config, "GEMINI_ENABLED", True)
    monkeypatch.setattr(Config, "GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(Config, "GEMINI_MODEL", MODEL_ID)
    monkeypatch.setattr(Config, "GEMINI_TIMEOUT_SECONDS", 30)


def test_gemini_disabled_does_not_create_client(monkeypatch):
    monkeypatch.setattr(Config, "GEMINI_ENABLED", False)
    monkeypatch.setattr(gemini_service, "_create_client", lambda *_args: pytest.fail("client created"))
    with pytest.raises(GeminiUnavailableError, match="disabled"):
        gemini_service.generate_answer("Giải thích API")


@pytest.mark.parametrize(
    ("value", "expected"),
    [("true", True), ("false", False), ("yes", True), ("no", False), ("1", True), ("0", False)],
)
def test_boolean_environment_parser(monkeypatch, value, expected):
    monkeypatch.setenv("TEST_BOOL", value)
    assert _get_bool("TEST_BOOL") is expected


@pytest.mark.parametrize("value", ["not-a-number", "0", "-5"])
def test_timeout_environment_parser_uses_safe_default(monkeypatch, value):
    monkeypatch.setenv("TEST_TIMEOUT", value)
    assert _get_positive_int("TEST_TIMEOUT", 10) == 10


def test_missing_api_key_uses_safe_error(monkeypatch):
    monkeypatch.setattr(Config, "GEMINI_API_KEY", "")
    with pytest.raises(GeminiUnavailableError, match="missing_api_key"):
        gemini_service.generate_answer("Giải thích API")


@pytest.mark.parametrize("model", [""])
def test_invalid_model_is_rejected_before_creating_client(monkeypatch, model):
    monkeypatch.setattr(Config, "GEMINI_MODEL", model)
    monkeypatch.setattr(gemini_service, "_create_client", lambda *_args: pytest.fail("client created"))
    with pytest.raises(GeminiUnavailableError, match="invalid_model"):
        gemini_service.generate_answer("Giải thích API")


def test_gemini_success(monkeypatch):
    calls = []
    monkeypatch.setattr(gemini_service, "_create_client", lambda api_key, timeout: calls.append((api_key, timeout)) or object())
    monkeypatch.setattr(
        gemini_service,
        "_generate",
        lambda _client, model, message: calls.append((model, message)) or SimpleNamespace(text="  API là giao diện lập trình.  "),
    )
    result = gemini_service.generate_answer("API là gì?")
    assert calls == [("test-key-not-real", 30), ("gemini-3.5-flash", "API là gì?")]
    assert result == {
        "answer": "API là giao diện lập trình.",
        "source": {"type": "gemini", "title": "Gemini AI", "url": None},
        "ai_generated": True,
        "fallback_used": False,
    }


def test_gemini_answer_style_is_bounded_and_safe_for_plain_text_ui():
    assert 200 <= GEMINI_MAX_OUTPUT_TOKENS <= 600
    assert "80-180 từ" in SYSTEM_INSTRUCTION
    assert 'dùng dấu "•"' in SYSTEM_INSTRUCTION
    assert "Không dùng bảng, HTML" in SYSTEM_INSTRUCTION
    assert "Không bịa nguồn" in SYSTEM_INSTRUCTION
    assert "thông tin chính thức" in SYSTEM_INSTRUCTION


def test_gemini_markdown_is_converted_to_plain_text():
    raw = "## Khái niệm\n\n**Hệ thống thông tin** gồm:\n- Con người\n- Công nghệ"
    assert _to_plain_text(raw) == "Khái niệm\n\nHệ thống thông tin gồm:\n• Con người\n• Công nghệ"


def test_empty_gemini_response(monkeypatch):
    monkeypatch.setattr(gemini_service, "_create_client", lambda *_args: object())
    monkeypatch.setattr(gemini_service, "_generate", lambda *_args: SimpleNamespace(text="  "))
    with pytest.raises(GeminiUnavailableError, match="empty_response"):
        gemini_service.generate_answer("API là gì?")


class FakeGeminiError(Exception):
    def __init__(self, message, status_code=None):
        self.status_code = status_code
        super().__init__(message)


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (TimeoutError("request timed out"), "timeout"),
        (FakeGeminiError("DEADLINE_EXCEEDED", 504), "timeout"),
        (FakeGeminiError("RESOURCE_EXHAUSTED quota", 429), "quota_exceeded"),
        (ConnectionError("network connection failed"), "network_error"),
        (FakeGeminiError("UNAUTHENTICATED", 401), "authentication_error"),
        (FakeGeminiError("model not found", 404), "invalid_model"),
        (ValueError("unexpected"), "unexpected_error"),
    ],
)
def test_gemini_errors_are_normalized(monkeypatch, error, reason):
    monkeypatch.setattr(gemini_service, "_create_client", lambda *_args: object())
    monkeypatch.setattr(gemini_service, "_generate", lambda *_args: (_ for _ in ()).throw(error))
    with pytest.raises(GeminiUnavailableError, match=reason):
        gemini_service.generate_answer("API là gì?")


def test_gemini_error_log_does_not_expose_secret(monkeypatch, caplog):
    secret = "test-secret-that-must-not-be-logged"
    monkeypatch.setattr(gemini_service, "_create_client", lambda *_args: object())
    monkeypatch.setattr(
        gemini_service,
        "_generate",
        lambda *_args: (_ for _ in ()).throw(ValueError(f"request failed {secret}")),
    )
    with pytest.raises(GeminiUnavailableError, match="unexpected_error"):
        gemini_service.generate_answer("API là gì?")
    assert secret not in caplog.text


def test_faq_has_priority_and_never_calls_gemini(monkeypatch):
    monkeypatch.setattr(chat_service, "generate_answer", lambda _message: pytest.fail("Gemini called"))
    result = chat_service.get_chat_response("Mình muốn tra cứu học phí ở đâu?")
    assert result["intent"] == "faq"
    assert result["ai_generated"] is False
    assert result["fallback_used"] is False


@pytest.mark.parametrize("message", ["Giải thích điện toán đám mây là gì", "Thời tiết hôm nay"])
def test_knowledge_and_unknown_use_gemini_without_faq(monkeypatch, message):
    calls = []
    monkeypatch.setattr(chat_service, "generate_answer", lambda value: calls.append(value) or {
        "answer": "Câu trả lời AI", "source": {"type": "gemini", "title": "Gemini AI", "url": None},
        "ai_generated": True, "fallback_used": False,
    })
    result = chat_service.get_chat_response(message)
    assert calls == [message]
    assert result["source"]["type"] == "gemini"
    assert result["ai_generated"] is True


def test_gemini_failure_uses_complete_fallback(monkeypatch):
    monkeypatch.setattr(chat_service, "generate_answer", lambda _message: (_ for _ in ()).throw(GeminiUnavailableError("timeout")))
    result = chat_service.get_chat_response("Giải thích điện toán đám mây là gì")
    assert result["source"] == {"type": "fallback", "title": "Phản hồi dự phòng", "url": None}
    assert result["ai_generated"] is False
    assert result["fallback_used"] is True
    assert {"answer", "intent", "source", "invalid", "paragraphs", "list", "sources", "data"} <= result.keys()


@pytest.mark.parametrize(
    "reason",
    ["disabled", "missing_api_key", "invalid_model", "quota_exceeded", "timeout", "authentication_error", "network_error", "empty_response", "unexpected_error"],
)
def test_gemini_failure_keeps_chat_api_http_200(monkeypatch, reason):
    monkeypatch.setattr(chat_service, "generate_answer", lambda _message: (_ for _ in ()).throw(GeminiUnavailableError(reason)))
    response = create_app({"TESTING": True}).test_client().post(
        "/api/chat", json={"message": "Giải thích điện toán đám mây là gì"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ai_generated"] is False
    assert data["fallback_used"] is True
    assert data["source"]["type"] == "fallback"


@pytest.mark.parametrize(
    "message",
    [
        "Tuần này tôi học môn gì?",
        "Tôi còn bài tập nào chưa làm?",
        "Deadline nào sắp hết hạn?",
        "Tuần này tôi có kiểm tra không?",
        "Tôi có thông báo mới chưa đọc không?",
        "Ghi chú hỏi giảng viên",
        "Nhắc tôi làm bài lúc 19 giờ",
    ],
)
def test_personal_features_never_call_gemini(monkeypatch, message):
    monkeypatch.setattr(chat_service, "generate_answer", lambda _message: pytest.fail("Gemini called"))
    result = chat_service.get_chat_response(message, {"id": "SV001"})
    assert result["ai_generated"] is False
    assert result["fallback_used"] is False


def test_gemini_api_response_has_complete_frontend_contract(monkeypatch):
    monkeypatch.setattr(chat_service, "generate_answer", lambda _message: {
        "answer": "Câu trả lời AI",
        "source": {"type": "gemini", "title": "Gemini AI", "url": None},
        "ai_generated": True,
        "fallback_used": False,
    })
    data = create_app({"TESTING": True}).test_client().post(
        "/api/chat", json={"message": "Giải thích điện toán đám mây là gì"}
    ).get_json()
    assert {
        "answer", "intent", "source", "ai_generated", "fallback_used", "invalid",
        "paragraphs", "list", "sources", "data", "latency_ms", "message_id",
    } <= data.keys()
