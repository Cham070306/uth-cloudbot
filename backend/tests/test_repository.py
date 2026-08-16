import pytest

from app import create_app
from repositories import get_repository, reset_repository_cache
from repositories.local import LocalRepository
from scripts.seed_data import seed
from services.intent_service import classify_intent


def test_local_repository_has_required_seed_data():
    repository = LocalRepository()
    assert len(repository.list("faqs")) == 150
    assert len(repository.list("documents")) == 30
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
    assert first == {
        "faqs": 150,
        "documents": 30,
        "students": 10,
        "schedules": 60,
        "assignments": 35,
        "exams": 20,
        "announcements": 30,
    }


def test_seed_populates_an_empty_remote_repository_idempotently():
    class EmptyRemote:
        def __init__(self): self.data = {}
        def upsert(self, collection, item): self.data.setdefault(collection, {})[item["id"]] = dict(item)

    remote = EmptyRemote()
    first = seed(repository=remote)
    second = seed(repository=remote)
    assert first == second
    assert len(remote.data["faqs"]) == 150
    assert len(remote.data["documents"]) == 30


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
    headers = {"Authorization": "Bearer demo-token-sv001"}
    chat = client.post("/api/chat", json={"message": "Học phí xem ở đâu?"}, headers=headers).get_json()
    conversation = repository.get("conversations", chat["message_id"])
    assert conversation["question"] == "Học phí xem ở đâu?"
    assert conversation["student_id"] == "SV001"
    assert conversation["created_at"]
    response = client.post("/api/feedback", json={"message_id": chat["message_id"], "helpful": True})
    assert response.status_code == 200
    feedback = repository.list("feedback")[0]
    assert feedback["message_id"] == chat["message_id"]
    assert feedback["created_at"]


def test_firestore_adapter_round_trips_runtime_record_with_fake_client():
    from repositories.firestore import FirestoreRepository

    class Snapshot:
        def __init__(self, item_id, value): self.id, self.value = item_id, value
        @property
        def exists(self): return self.value is not None
        def to_dict(self): return dict(self.value)

    class Document:
        def __init__(self, collection, item_id): self.collection, self.item_id = collection, item_id
        def set(self, value, merge=True): self.collection.data[self.item_id] = {**self.collection.data.get(self.item_id, {}), **value}
        def get(self): return Snapshot(self.item_id, self.collection.data.get(self.item_id))

    class Collection:
        def __init__(self): self.data, self.filters = {}, []
        def document(self, item_id): return Document(self, item_id)
        def where(self, key, operator, value): self.filters.append((key, value)); return self
        def stream(self):
            return [
                Snapshot(item_id, value) for item_id, value in self.data.items()
                if all(value.get(key) == expected for key, expected in self.filters)
            ]

    class Client:
        def __init__(self): self.collections = {}
        def collection(self, name): return self.collections.setdefault(name, Collection())

    repository = FirestoreRepository.__new__(FirestoreRepository)
    repository.client, repository.prefix = Client(), "uth_cloudbot"
    item = {"id": "note-demo", "student_id": "SV001", "content": "Nội dung demo", "created_at": "2026-08-16T10:00:00+07:00"}
    repository.upsert("notes", item)
    assert repository.get("notes", "note-demo") == item
    assert repository.list("notes", student_id="SV001") == [item]


def test_invalid_data_backend_has_clear_error(monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "invalid")
    reset_repository_cache()
    with pytest.raises(RuntimeError, match="DATA_BACKEND"):
        get_repository()
    monkeypatch.setenv("DATA_BACKEND", "local")
    reset_repository_cache()
