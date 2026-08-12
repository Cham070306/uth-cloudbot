from functools import wraps

from flask import g, jsonify, request

from services.student_service import get_student_by_token


def authenticate(username, password):
    from services.student_service import load_student_data

    for student in load_student_data()["students"]:
        if student["username"] == username and student["password"] == password:
            return {"access_token": student["token"], "student": public_student(student)}
    return None


def public_student(student):
    return {key: value for key, value in student.items() if key not in {"password", "token"}}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header[7:].strip() if header.startswith("Bearer ") else ""
        student = get_student_by_token(token)
        if student is None:
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Token đăng nhập không hợp lệ."}}), 401
        g.student = student
        return view(*args, **kwargs)

    return wrapped
