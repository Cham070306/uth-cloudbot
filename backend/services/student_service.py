from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from repositories import get_repository


TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def load_student_data():
    repository = get_repository()
    return {name: repository.list(name) for name in ("students", "schedules", "assignments", "exams", "announcements")}


def get_student_by_token(token):
    return next(iter(get_repository().list("students", token=token)), None)


def _owned(collection, student_id):
    return get_repository().list(collection, student_id=student_id)


def get_schedule(student_id, start=None, end=None):
    items = _owned("schedules", student_id)
    if start:
        items = [item for item in items if item["date"] >= start]
    if end:
        items = [item for item in items if item["date"] <= end]
    return sorted(items, key=lambda item: (item["date"], item["start_time"]))


def get_assignments(student_id, status=None):
    items = _owned("assignments", student_id)
    now = datetime.now(TIMEZONE)
    for item in items:
        due = datetime.fromisoformat(item["due_at"])
        if item["status"] not in {"completed", "submitted"} and due < now:
            item["status"] = "overdue"
        item["hours_remaining"] = round((due - now).total_seconds() / 3600, 1)
    if status:
        items = [item for item in items if item["status"] == status]
    return sorted(items, key=lambda item: item["due_at"])


def get_upcoming_assignments(student_id, hours=72):
    return [
        item for item in get_assignments(student_id)
        if item["status"] not in {"completed", "submitted", "overdue"}
        and 0 <= item["hours_remaining"] <= hours
    ]


def get_exams(student_id):
    return sorted(_owned("exams", student_id), key=lambda item: item["start_at"])


def get_announcements(student_id, unread_only=False):
    items = _owned("announcements", student_id)
    if unread_only:
        items = [item for item in items if not item.get("read", False)]
    return sorted(items, key=lambda item: item["published_at"], reverse=True)


def current_week_range(now=None):
    now = now or datetime.now(TIMEZONE)
    monday = now.date() - timedelta(days=now.weekday())
    return monday.isoformat(), (monday + timedelta(days=6)).isoformat()
