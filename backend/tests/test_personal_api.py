from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app import create_app
from services.action_service import reset_actions


AUTH = {"Authorization": "Bearer demo-token-sv001"}


@pytest.fixture()
def client():
    reset_actions()
    return create_app({"TESTING": True}).test_client()


def test_login_and_profile(client):
    login = client.post("/api/auth/login", json={"username": "sv001", "password": "demo123"})
    assert login.status_code == 200
    assert login.get_json()["access_token"] == "demo-token-sv001"
    profile = client.get("/api/me", headers=AUTH)
    assert profile.status_code == 200
    assert profile.get_json()["id"] == "SV001"
    assert "password" not in profile.get_json()


def test_personal_endpoints_require_login(client):
    assert client.get("/api/me/schedule").status_code == 401
    assert client.get("/api/me/assignments").status_code == 401


def test_student_only_sees_owned_data(client):
    data = client.get("/api/me/schedule", headers=AUTH).get_json()["items"]
    assert data
    assert {item["student_id"] for item in data} == {"SV001"}


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("Tuần này tôi học môn gì?", "personal_schedule"),
        ("Tôi còn bài tập nào chưa làm?", "personal_assignment"),
        ("Deadline nào sắp hết hạn?", "personal_deadline"),
        ("Tuần này tôi có kiểm tra không?", "personal_exam"),
        ("Tôi có thông báo mới chưa đọc không?", "personal_announcement"),
    ],
)
def test_chat_uses_authenticated_student_context(client, message, intent):
    response = client.post("/api/chat", json={"message": message}, headers=AUTH)
    data = response.get_json()
    assert response.status_code == 200
    assert data["intent"] == intent
    assert data["source"]["type"] == "mock_student_data"
    assert isinstance(data["data"]["items"], list)


def test_personal_chat_without_login_requests_authentication(client):
    data = client.post("/api/chat", json={"message": "Tuần này tôi học môn gì?"}).get_json()
    assert data["requires_authentication"] is True


def test_note_and_reminder_confirmation_flow(client):
    note = client.post("/api/me/notes", json={"content": "Hỏi giảng viên chương 3"}, headers=AUTH)
    assert note.status_code == 201
    note_item = note.get_json()
    assert note_item["status"] == "awaiting_confirmation"
    assert client.post(f"/api/me/notes/{note_item['id']}/confirm", headers=AUTH).get_json()["status"] == "active"
    remind_at = (datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) + timedelta(hours=1)).isoformat()
    reminder = client.post(
        "/api/me/reminders",
        json={"content": "Làm bài Cloud", "remind_at": remind_at}, headers=AUTH,
    )
    assert reminder.status_code == 201
    item = reminder.get_json()
    assert item["status"] == "awaiting_confirmation"
    confirmed = client.post(f"/api/me/reminders/{item['id']}/confirm", headers=AUTH)
    assert confirmed.get_json()["status"] == "scheduled"


def test_reminder_requires_timezone_and_normalizes_to_vietnam(client):
    missing_timezone = client.post(
        "/api/me/reminders",
        json={"content": "Không có múi giờ", "remind_at": "2026-08-13T20:00:00"}, headers=AUTH,
    )
    assert missing_timezone.status_code == 400
    utc_reminder = client.post(
        "/api/me/reminders",
        json={"content": "UTC demo", "remind_at": "2026-08-13T13:00:00Z"}, headers=AUTH,
    )
    assert utc_reminder.status_code == 201
    assert utc_reminder.get_json()["remind_at"] == "2026-08-13T20:00:00+07:00"


def test_chat_actions_require_confirmation(client):
    for message in ("Ghi chú hỏi giảng viên", "Nhắc tôi làm bài lúc 19 giờ"):
        data = client.post("/api/chat", json={"message": message}, headers=AUTH).get_json()
        assert data["requires_confirmation"] is True
        assert data["confirmation"]["raw_message"] == message


def test_due_reminder_is_marked_sent(client):
    remind_at = (datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) - timedelta(minutes=1)).isoformat()
    item = client.post(
        "/api/me/reminders", json={"content": "Nhắc quá hạn", "remind_at": remind_at}, headers=AUTH,
    ).get_json()
    client.post(f"/api/me/reminders/{item['id']}/confirm", headers=AUTH)
    reminders = client.get("/api/me/reminders", headers=AUTH).get_json()["items"]
    sent = next(reminder for reminder in reminders if reminder["id"] == item["id"])
    assert sent["status"] == "sent"
    assert "sent_at" in sent
