import json
from pathlib import Path

import pytest

from services.faq_service import find_faq, load_faqs, searchable_question_count
from services.intent_service import classify_intent, normalize_text
from services.student_service import current_week_range, get_remaining_schedule, get_schedule


def test_faq_dataset_has_unique_ids_and_required_fields():
    faqs = load_faqs()
    assert len(faqs) == 150
    assert len({faq["id"] for faq in faqs}) == 150
    assert len({faq["answer"] for faq in faqs}) == 150
    assert faqs[0]["id"] == "faq-001"
    assert faqs[-1]["id"] == "faq-150"
    assert [faq["id"] for faq in faqs] == [f"faq-{index:03d}" for index in range(1, 151)]
    assert searchable_question_count() >= 750
    normalized_questions = []
    for faq in faqs:
        assert {"id", "question", "keywords", "answer", "source", "updated_at"} <= faq.keys()
        assert faq["question"].strip() and faq["answer"].strip()
        assert len(faq["answer"]) >= 300
        assert "phụ thuộc kế hoạch và quy định áp dụng" not in faq["answer"]
        assert len(faq["keywords"]) >= 3
        assert all(isinstance(keyword, str) and keyword.strip() for keyword in faq["keywords"])
        normalized_keywords = [normalize_text(keyword) for keyword in faq["keywords"]]
        assert len(normalized_keywords) == len(set(normalized_keywords)), faq["id"]
        assert isinstance(faq["source"], dict)
        assert isinstance(faq["source"].get("title"), str) and faq["source"]["title"].strip()
        normalized_questions.append(normalize_text(faq["question"]))
    assert len(normalized_questions) == len(set(normalized_questions))
    structured_markers = ("Cách xử lý:", "Nội dung cần kiểm tra:", "Các bước tra cứu:", "Quy trình đề xuất:")
    assert sum(any(marker in faq["answer"] for faq in faqs) for marker in structured_markers) == 4


def test_faq_evaluation_dataset_is_valid():
    root = Path(__file__).resolve().parents[2]
    cases = json.loads((root / "data/evaluation/faq_questions.json").read_text(encoding="utf-8"))["cases"]
    faq_ids = {faq["id"] for faq in load_faqs()}
    assert len(cases) >= 300
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(case["expected_faq_id"] in faq_ids for case in cases)
    assert all(case["expected_intent"] == "faq" for case in cases)
    assert all(case["must_not_use_gemini"] is True for case in cases)


def test_every_faq_question_and_keyword_resolves_to_its_owner():
    for faq in load_faqs():
        for text in [faq["question"], *faq.get("keywords", [])]:
            assert find_faq(text)["id"] == faq["id"], text


@pytest.mark.parametrize(
    ("message", "faq_id"),
    [
        ("cho mình hỏi cách dkhp", "faq-001"),
        ("mình muốn xem hphi", "faq-003"),
        ("quên mk cổng sinh viên", "faq-004"),
        ("đăng kí học phầnn ở đâu", "faq-001"),
        ("xin cấp lại thẻ sinh viê", "faq-009"),
        ("đăng ký ktx như nào", "faq-025"),
        ("đóng bhyt ở đâu", "faq-026"),
    ],
)
def test_faq_recognizes_chat_abbreviations_and_minor_typos(message, faq_id):
    assert find_faq(message)["id"] == faq_id


def test_normalize_text_handles_vietnamese():
    assert normalize_text("Đăng ký HỌC phần!") == "dang ky hoc phan"


def test_intent_priority_distinguishes_exam_schedule():
    assert classify_intent("Lịch thi cuối kỳ") == "exam_schedule"
    assert classify_intent("Lịch học hôm nay") == "schedule"


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("Lịch thi của tôi tuần này", "personal_exam"),
        ("Tôi thi môn gì?", "personal_exam"),
        ("Thời khóa biểu của mình", "personal_schedule"),
        ("Ngày mai học gì?", "personal_schedule"),
    ],
)
def test_personal_schedule_phrasings_take_priority(message, intent):
    assert classify_intent(message) == intent


def test_remaining_schedule_excludes_classes_that_already_ended():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime(2026, 8, 19, 12, 30, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    items = get_remaining_schedule("SV001", "2026-08-17", "2026-08-23", now=now)
    assert [item["id"] for item in items] == [
        "schedule-003", "schedule-004", "schedule-005", "schedule-006",
    ]


def test_current_week_schedule_rolls_demo_dates_forward():
    start, end = current_week_range()
    items = get_schedule("SV001", start, end)

    assert len(items) == 6
    assert items[0]["date"] == start
    assert items[-1]["date"] <= end


def test_find_faq_rejects_unrelated_question():
    assert find_faq("Thời tiết hôm nay thế nào?") is None
    assert find_faq("Giới thiệu chung về Trường Đại học Giao thông vận tải Thành phố Hồ Chí Minh") is None
