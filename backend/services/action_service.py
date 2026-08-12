from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from repositories import get_repository

TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

def reset_actions(): get_repository().clear_runtime()
def list_notes(student_id): return get_repository().list("notes", student_id=student_id)
def list_reminders(student_id): return get_repository().list("reminders", student_id=student_id)

def create_note(student_id, content):
    return get_repository().upsert("notes", {"id": f"note-{uuid4().hex[:12]}", "student_id": student_id, "content": content, "status": "awaiting_confirmation", "created_at": datetime.now(TIMEZONE).isoformat()})

def update_note(student_id, note_id, action):
    item = get_repository().get("notes", note_id)
    if item is None or item.get("student_id") != student_id: return None
    item["status"] = "active" if action == "confirm" else "cancelled"
    return get_repository().upsert("notes", item)

def create_reminder(student_id, content, remind_at):
    parsed = datetime.fromisoformat(remind_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("remind_at must include a timezone offset")
    normalized = parsed.astimezone(TIMEZONE).isoformat()
    return get_repository().upsert("reminders", {"id": f"reminder-{uuid4().hex[:12]}", "student_id": student_id, "content": content, "remind_at": normalized, "status": "awaiting_confirmation", "created_at": datetime.now(TIMEZONE).isoformat()})

def update_reminder(student_id, reminder_id, action):
    item = get_repository().get("reminders", reminder_id)
    if item is None or item.get("student_id") != student_id: return None
    item["status"] = {"confirm": "scheduled", "complete": "completed", "cancel": "cancelled"}[action]
    return get_repository().upsert("reminders", item)

def process_due_reminders(now=None):
    now = now or datetime.now(TIMEZONE); due = []
    for item in get_repository().list("reminders"):
        if item["status"] == "scheduled" and datetime.fromisoformat(item["remind_at"]) <= now:
            item.update(status="sent", sent_at=now.isoformat()); due.append(get_repository().upsert("reminders", item))
    return due
