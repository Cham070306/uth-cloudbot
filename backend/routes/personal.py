from flask import g, jsonify, request

from routes import api
from services.action_service import (
    create_note, create_reminder, list_notes, list_reminders, process_due_reminders, update_note,
    update_reminder,
)
from services.auth_service import login_required, public_student
from services.student_service import (
    get_announcements, get_assignments, get_exams, get_schedule, get_upcoming_assignments,
)


def invalid(message):
    return jsonify({"error": {"code": "INVALID_REQUEST", "message": message}}), 400


@api.get("/me")
@login_required
def me():
    return jsonify(public_student(g.student))


@api.get("/me/schedule")
@login_required
def schedule():
    return jsonify({"items": get_schedule(g.student["id"], request.args.get("from"), request.args.get("to"))})


@api.get("/me/assignments")
@login_required
def assignments():
    return jsonify({"items": get_assignments(g.student["id"], request.args.get("status"))})


@api.get("/me/assignments/upcoming")
@login_required
def upcoming_assignments():
    return jsonify({"items": get_upcoming_assignments(g.student["id"])})


@api.get("/me/exams")
@login_required
def exams():
    return jsonify({"items": get_exams(g.student["id"])})


@api.get("/me/announcements")
@login_required
def announcements():
    return jsonify({"items": get_announcements(g.student["id"], request.args.get("unread") == "true")})


@api.get("/me/notes")
@login_required
def notes():
    return jsonify({"items": list_notes(g.student["id"])})


@api.post("/me/notes")
@login_required
def add_note():
    payload = request.get_json(silent=True) or {}
    content = payload.get("content")
    if not isinstance(content, str) or not content.strip():
        return invalid("Trường content không được để trống.")
    return jsonify(create_note(g.student["id"], content.strip())), 201


@api.post("/me/notes/<note_id>/<action>")
@login_required
def note_action(note_id, action):
    if action not in {"confirm", "cancel"}:
        return invalid("Hành động note không hợp lệ.")
    item = update_note(g.student["id"], note_id, action)
    if item is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Không tìm thấy note."}}), 404
    return jsonify(item)


@api.get("/me/reminders")
@login_required
def reminders():
    process_due_reminders()
    return jsonify({"items": list_reminders(g.student["id"])})


@api.post("/me/reminders")
@login_required
def add_reminder():
    payload = request.get_json(silent=True) or {}
    try:
        item = create_reminder(g.student["id"], payload.get("content", "").strip(), payload.get("remind_at", ""))
    except (AttributeError, TypeError, ValueError):
        return invalid("content và remind_at ISO-8601 phải hợp lệ.")
    if not item["content"]:
        return invalid("Trường content không được để trống.")
    return jsonify(item), 201


@api.post("/me/reminders/<reminder_id>/<action>")
@login_required
def reminder_action(reminder_id, action):
    if action not in {"confirm", "complete", "cancel"}:
        return invalid("Hành động reminder không hợp lệ.")
    item = update_reminder(g.student["id"], reminder_id, action)
    if item is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Không tìm thấy reminder."}}), 404
    return jsonify(item)
