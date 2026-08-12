import pytest

from app import create_app
from repositories import get_repository, reset_repository_cache
from repositories.local import LocalRepository
from scripts.seed_data import seed
from services.intent_service import classify_intent


def test_local_repository_has_required_seed_data():
    repository = LocalRepository()
    assert len(repository.list("faqs")) >= 30
    assert len(repository.list("documents")) >= 10
    assert repository.list("schedules")
    assert repository.list("assignments")
    assert repository.list("exams")
    assert repository.list("announcements")


def test_local_repository_upsert_is_idempotent():
    repository = LocalRepository()
    item = {"id": "note-test", "student_id": "SV001", "content": "demo"}
    repository.upsert("notes", item)
    repository.upsert("notes", {**item, "content": "updated"})
    assert repository.list("notes") == [{**item, "content": "updated"}]


def test_seed_can_run_repeatedly():
    first = seed()
    second = seed()
    assert first == second
    assert first["faqs"] >= 30 and first["documents"] >= 10


def test_seed_populates_an_empty_remote_repository_idempotently():
    class EmptyRemote:
        def __init__(self): self.data = {}
        def upsert(self, collection, item): self.data.setdefault(collection, {})[item["id"]] = dict(item)

    remote = EmptyRemote()
    first = seed(repository=remote)
    second = seed(repository=remote)
    assert first == second
    assert len(remote.data["faqs"]) == 30
    assert len(remote.data["documents"]) == 10


@pytest.mark.parametrize(("message", "intent"), [
    ("Lịch thi của tôi tuần này", "exam_schedule"),
    ("Tôi học môn gì tuần này", "personal_schedule"),
    ("Toi con bai tap nao chua nop", "personal_assignment"),
    ("Nhắc tôi nộp bài lúc 20 giờ", "create_reminder"),
    ("ghi chu noi dung nay", "create_note"),
    ("thi", "unknown"),
    ("Tôi thích tài liệu nhưng đang hỏi học phí", "faq"),
    ("thời tiết hôm nay", "unknown"),
])
def test_intent_overlap_and_false_positives(message, intent):
    assert classify_intent(message) == intent


def test_conversation_and_feedback_are_persisted():
    repository = get_repository()
    repository.clear_runtime()
    client = create_app({"TESTING": True}).test_client()
    chat = client.post("/api/chat", json={"message": "Học phí xem ở đâu?"}).get_json()
    assert repository.get("conversations", chat["message_id"])["question"] == "Học phí xem ở đâu?"
    response = client.post("/api/feedback", json={"message_id": chat["message_id"], "helpful": True})
    assert response.status_code == 200
    assert repository.list("feedback")[0]["message_id"] == chat["message_id"]


def test_invalid_data_backend_has_clear_error(monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "invalid")
    reset_repository_cache()
    with pytest.raises(RuntimeError, match="DATA_BACKEND"):
        get_repository()
    monkeypatch.setenv("DATA_BACKEND", "local")
    reset_repository_cache()
