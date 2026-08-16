from services.faq_service import find_faq, load_faqs, searchable_question_count
from services.intent_service import classify_intent, normalize_text
from services.student_service import get_remaining_schedule


def test_faq_dataset_has_unique_ids_and_required_fields():
    faqs = load_faqs()
    assert len(faqs) >= 30
    assert searchable_question_count() >= 100
    assert len({faq["id"] for faq in faqs}) == len(faqs)
    for faq in faqs:
        assert {"id", "question", "answer", "source"} <= faq.keys()


def test_every_faq_question_and_keyword_resolves_to_its_owner():
    for faq in load_faqs():
        for text in [faq["question"], *faq.get("keywords", [])]:
            assert find_faq(text)["id"] == faq["id"], text


def test_normalize_text_handles_vietnamese():
    assert normalize_text("Đăng ký HỌC phần!") == "dang ky hoc phan"


def test_intent_priority_distinguishes_exam_schedule():
    assert classify_intent("Lịch thi cuối kỳ") == "exam_schedule"
    assert classify_intent("Lịch học hôm nay") == "schedule"


def test_remaining_schedule_excludes_classes_that_already_ended():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime(2026, 8, 12, 12, 30, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    items = get_remaining_schedule("SV001", "2026-08-10", "2026-08-16", now=now)
    assert [item["id"] for item in items] == ["schedule-003"]


def test_find_faq_rejects_unrelated_question():
    assert find_faq("Thời tiết hôm nay thế nào?") is None
