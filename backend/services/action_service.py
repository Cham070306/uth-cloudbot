from datetime import datetime
from itertools import count
from zoneinfo import ZoneInfo


TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
_ids = count(1)
_notes = []
_reminders = []


def reset_actions():
    _notes.clear()
    _reminders.clear()


def list_notes(student_id):
    return [item.copy() for item in _notes if item["student_id"] == student_id]


def create_note(student_id, content):
    item = {
        "id": f"note-{next(_ids):04d}", "student_id": student_id,
        "content": content, "status": "awaiting_confirmation", "created_at": datetime.now(TIMEZONE).isoformat(),
    }
    _notes.append(item)
    return item.copy()


def update_note(student_id, note_id, action):
    item = next((x for x in _notes if x["id"] == note_id and x["student_id"] == student_id), None)
    if item is None:
        return None
    item["status"] = "active" if action == "confirm" else "cancelled"
    return item.copy()


def list_reminders(student_id):
    return [item.copy() for item in _reminders if item["student_id"] == student_id]


def create_reminder(student_id, content, remind_at):
    datetime.fromisoformat(remind_at)
    item = {
        "id": f"reminder-{next(_ids):04d}", "student_id": student_id,
        "content": content, "remind_at": remind_at, "status": "awaiting_confirmation",
        "created_at": datetime.now(TIMEZONE).isoformat(),
    }
    _reminders.append(item)
    return item.copy()


def update_reminder(student_id, reminder_id, action):
    item = next((x for x in _reminders if x["id"] == reminder_id and x["student_id"] == student_id), None)
    if item is None:
        return None
    transitions = {"confirm": "scheduled", "complete": "completed", "cancel": "cancelled"}
    item["status"] = transitions[action]
    return item.copy()


def process_due_reminders(now=None):
    now = now or datetime.now(TIMEZONE)
    due = []
    for item in _reminders:
        if item["status"] == "scheduled" and datetime.fromisoformat(item["remind_at"]) <= now:
            item["status"] = "sent"
            item["sent_at"] = now.isoformat()
            due.append(item.copy())
    return due
