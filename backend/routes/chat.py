from time import perf_counter

from flask import current_app, jsonify, request

from routes import api
from services.chat_service import get_chat_response
from services.student_service import get_student_by_token


def invalid(message):
    return jsonify({"error": {"code": "INVALID_REQUEST", "message": message}}), 400


@api.post("/chat")
def chat():
    started_at = perf_counter()
    if not request.is_json:
        return invalid("Body phải có Content-Type application/json.")

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return invalid("Body phải là một JSON object hợp lệ.")

    # `question` is the FE-01 compatibility alias for canonical `message`.
    field = "message" if "message" in payload else "question" if "question" in payload else None
    if field is None:
        return invalid("Thiếu trường message.")
    message = payload[field]
    if not isinstance(message, str):
        return invalid("Trường message phải là chuỗi.")
    message = message.strip()
    if not message:
        return invalid("Trường message không được để trống.")
    if len(message) > current_app.config["MAX_MESSAGE_LENGTH"]:
        return invalid(
            f"Trường message không được vượt quá {current_app.config['MAX_MESSAGE_LENGTH']} ký tự."
        )

    header = request.headers.get("Authorization", "")
    token = header[7:].strip() if header.startswith("Bearer ") else ""
    student = get_student_by_token(token) if token else None
    result = get_chat_response(message, student)
    result["latency_ms"] = max(0, int((perf_counter() - started_at) * 1000))
    return jsonify(result)
