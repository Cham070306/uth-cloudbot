import pytest

from config import Config


@pytest.fixture(autouse=True)
def disable_real_gemini(monkeypatch):
    """Prevent any test from using ambient Gemini credentials or the real API."""
    monkeypatch.setattr(Config, "GEMINI_ENABLED", False)
    monkeypatch.setattr(Config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(Config, "GEMINI_MODEL", "")

