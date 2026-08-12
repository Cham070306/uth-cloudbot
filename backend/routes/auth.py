from flask import jsonify, request

from routes import api
from services.auth_service import authenticate


@api.post("/auth/login")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": {"code": "INVALID_REQUEST", "message": "Body JSON không hợp lệ."}}), 400
    result = authenticate(payload.get("username"), payload.get("password"))
    if result is None:
        return jsonify({"error": {"code": "INVALID_CREDENTIALS", "message": "Tài khoản hoặc mật khẩu không đúng."}}), 401
    return jsonify(result)
