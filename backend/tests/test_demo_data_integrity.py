from datetime import datetime, timedelta

from app import create_app
from repositories.local import LocalRepository


EXPECTED_COUNTS = {
    "students": 10,
    "schedules": 390,
    "assignments": 35,
    "exams": 20,
    "announcements": 30,
    "documents": 30,
    "faqs": 150,
}
REQUIRED = {
    "students": {"id", "username", "password", "token", "full_name", "email", "class_code", "major", "semester", "timezone"},
    "schedules": {"id", "student_id", "course_code", "course_name", "date", "start_time", "end_time", "room", "lecturer"},
    "assignments": {"id", "student_id", "course_code", "course_name", "title", "platform", "due_at", "status"},
    "exams": {"id", "student_id", "course_code", "course_name", "type", "title", "start_at", "end_at", "room", "platform"},
    "announcements": {"id", "student_id", "title", "content", "priority", "published_at", "read"},
    "documents": {"id", "title", "category", "url", "updated_at"},
}


def repository():
    return LocalRepository()


def test_demo_collection_counts_ids_and_required_fields():
    repo = repository()
    for collection, expected in EXPECTED_COUNTS.items():
        items = repo.list(collection)
        assert len(items) == expected
        assert len({item["id"] for item in items}) == expected
        if collection in REQUIRED:
            for item in items:
                assert REQUIRED[collection] <= item.keys()
                for key in REQUIRED[collection] - {"room", "platform", "url"}:
                    assert item[key] is not None and item[key] != "", (collection, item["id"], key)


def test_student_profiles_are_unique_safe_and_in_range():
    students = repository().list("students")
    assert len({item["username"] for item in students}) == len(students)
    assert len({item["token"] for item in students}) == len(students)
    assert len({item["student_code"] for item in students}) == len(students)
    forbidden = {"cccd", "national_id", "home_address", "bank_account"}
    for student in students:
        assert student["email"].endswith("@example.com")
        assert 0 <= student["gpa"] <= 4
        assert 0 <= student["conduct_score"] <= 100
        assert 0 <= student["accumulated_credits"] <= student["required_credits"]
        assert not (forbidden & student.keys())


def test_student_links_course_catalog_and_timestamps_are_consistent():
    repo = repository()
    student_ids = {item["id"] for item in repo.list("students")}
    course_names = {}
    for collection in ("schedules", "assignments", "exams"):
        for item in repo.list(collection):
            assert item["student_id"] in student_ids
            previous = course_names.setdefault(item["course_code"], item["course_name"])
            assert previous == item["course_name"]
    for item in repo.list("announcements"):
        assert item["student_id"] in student_ids
        datetime.fromisoformat(item["published_at"])
    for item in repo.list("assignments"):
        datetime.fromisoformat(item["due_at"])
        assert item["status"] in {"pending", "in_progress", "submitted", "overdue"}


def _assert_no_overlap(items, start_value, end_value, group_value):
    grouped = {}
    for item in items:
        grouped.setdefault(group_value(item), []).append((start_value(item), end_value(item), item["id"]))
    for intervals in grouped.values():
        intervals.sort()
        for previous, current in zip(intervals, intervals[1:]):
            assert previous[1] <= current[0], (previous[2], current[2])


def test_schedule_and_exam_times_are_valid_without_student_conflicts():
    repo = repository()
    schedules = repo.list("schedules")
    for item in schedules:
        assert item["start_time"] < item["end_time"]
        datetime.fromisoformat(item["date"])
    _assert_no_overlap(
        schedules,
        lambda item: datetime.fromisoformat(f'{item["date"]}T{item["start_time"]}'),
        lambda item: datetime.fromisoformat(f'{item["date"]}T{item["end_time"]}'),
        lambda item: (item["student_id"], item["date"]),
    )
    exams = repo.list("exams")
    for item in exams:
        start, end = datetime.fromisoformat(item["start_at"]), datetime.fromisoformat(item["end_at"])
        assert start < end
        if item["type"] == "online":
            assert item["room"] is None and item["platform"]
        else:
            assert item["room"] and item["platform"] is None
    _assert_no_overlap(
        exams,
        lambda item: datetime.fromisoformat(item["start_at"]),
        lambda item: datetime.fromisoformat(item["end_at"]),
        lambda item: item["student_id"],
    )


def test_every_student_has_weekly_schedule_through_september():
    schedules = repository().list("schedules")
    expected_dates = {
        (datetime(2026, 8, 17) + timedelta(days=offset)).date().isoformat()
        for offset in range(45)
        if (datetime(2026, 8, 17) + timedelta(days=offset)).weekday() < 6
    }

    for student_number in range(1, 11):
        student_id = f"SV{student_number:03d}"
        actual_dates = {
            item["date"] for item in schedules if item["student_id"] == student_id
        }
        assert actual_dates == expected_dates


def test_demo_api_contracts_and_private_fields():
    client = create_app({"TESTING": True}).test_client()
    login = client.post("/api/auth/login", json={"username": "sv001", "password": "demo123"})
    assert login.status_code == 200
    token = login.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    profile = client.get("/api/me", headers=headers).get_json()
    assert "password" not in profile and "token" not in profile
    assert profile["student_code"] == "DEMO2026001"
    for endpoint in ("schedule", "assignments", "exams", "announcements"):
        response = client.get(f"/api/me/{endpoint}", headers=headers)
        assert response.status_code == 200 and response.get_json()["items"]
    documents = client.get("/api/documents")
    assert documents.status_code == 200 and len(documents.get_json()["items"]) == 30
    personal_chat = client.post("/api/chat", json={"message": "Tôi còn bài tập nào chưa làm?"}, headers=headers)
    assert personal_chat.status_code == 200
    assert personal_chat.get_json()["intent"] == "personal_assignment"
