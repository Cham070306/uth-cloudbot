import os


def _get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_positive_int(name, default):
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


class Config:
    MAX_CONTENT_LENGTH = 16 * 1024
    MAX_MESSAGE_LENGTH = 2000
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    DATA_BACKEND = os.getenv("DATA_BACKEND", "local")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    FIRESTORE_COLLECTION_PREFIX = os.getenv("FIRESTORE_COLLECTION_PREFIX", "uth_cloudbot")
    GEMINI_ENABLED = _get_bool("GEMINI_ENABLED", False)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip()
    GEMINI_TIMEOUT_SECONDS = _get_positive_int("GEMINI_TIMEOUT_SECONDS", 10)


def get_port():
    try:
        port = int(os.getenv("PORT", "8080"))
    except ValueError:
        return 8080
    return port if 1 <= port <= 65535 else 8080
