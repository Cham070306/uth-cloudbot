from flask import jsonify, request
from datetime import datetime, timezone
from uuid import uuid4

from routes import api
from repositories import get_repository


def invalid(message):
    return jsonify({"error": {"code": "INVALID_REQUEST", "message": message}}), 400


@api.post("/feedback")
def feedback():
    if not request.is_json:
        return invalid("Body phải có Content-Type application/json.")
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return invalid("Body phải là một JSON object hợp lệ.")

    # Accept FE-01's question/answer/vote payload without persisting it.
    legacy = "message_id" not in payload and any(k in payload for k in ("question", "answer", "vote"))
    if legacy:
        question = payload.get("question")
        vote = payload.get("vote")
        if not isinstance(question, str) or not question.strip():
            return invalid("Trường question không được để trống.")
        if vote not in ("up", "down"):
            return invalid("Trường vote phải là 'up' hoặc 'down'.")
        feedback_id = f"feedback-{uuid4().hex[:12]}"
        get_repository().upsert("feedback", {
            "id": feedback_id, "message_id": None, "question": question.strip(),
            "answer": payload.get("answer", ""), "vote": vote, "helpful": vote == "up",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return jsonify({
            "status": "received",
            "message_id": feedback_id,
            "helpful": vote == "up",
        })

    if "message_id" not in payload:
        return invalid("Thiếu trường message_id.")
    message_id = payload["message_id"]
    if not isinstance(message_id, str) or not message_id.strip():
        return invalid("Trường message_id phải là chuỗi không rỗng.")
    if "helpful" not in payload:
        return invalid("Thiếu trường helpful.")
    helpful = payload["helpful"]
    if type(helpful) is not bool:
        return invalid("Trường helpful phải là boolean.")

    get_repository().upsert("feedback", {
        "id": f"feedback-{uuid4().hex[:12]}", "message_id": message_id.strip(),
        "helpful": helpful, "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return jsonify({"status": "received", "message_id": message_id.strip(), "helpful": helpful})
