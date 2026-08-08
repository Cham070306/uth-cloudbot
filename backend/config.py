import os


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


def get_port():
    try:
        port = int(os.getenv("PORT", "8080"))
    except ValueError:
        return 8080
    return port if 1 <= port <= 65535 else 8080
