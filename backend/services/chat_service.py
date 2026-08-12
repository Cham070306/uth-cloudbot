from services.faq_service import build_faq_response, find_faq
from services.intent_service import classify_intent
from services.mock_chat_service import get_mock_response
from services.student_service import (
    current_week_range, get_announcements, get_assignments, get_exams, get_schedule,
    get_upcoming_assignments,
)


def _personal_response(answer, intent, items, student_id):
    return {
        "answer": answer,
        "intent": intent,
        "data": {"items": items},
        "source": {"type": "mock_student_data", "title": f"Dữ liệu giả lập của {student_id}", "url": None},
        "updated_at": None,
        "invalid": False,
        "paragraphs": [answer],
        "list": [],
        "sources": [{"label": f"Dữ liệu giả lập của {student_id}", "url": None}],
        "requires_confirmation": False,
        "confirmation": None,
    }


def get_chat_response(message, student=None):
    intent = classify_intent(message)
    personal_intents = {
        "personal_schedule", "personal_assignment", "personal_deadline", "personal_exam",
        "personal_announcement", "create_note", "create_reminder",
    }
    if intent in personal_intents and student is None:
        result = get_mock_response(message)
        result.update({
            "intent": intent, "answer": "Bạn cần đăng nhập để xem hoặc thay đổi dữ liệu cá nhân.",
            "requires_authentication": True,
        })
        result["paragraphs"] = [result["answer"]]
        return result

    if student is not None:
        student_id = student["id"]
        if intent == "personal_schedule":
            start, end = current_week_range()
            items = get_schedule(student_id, start, end)
            return _personal_response(f"Tuần này bạn có {len(items)} buổi học.", intent, items, student_id)
        if intent == "personal_assignment":
            items = [x for x in get_assignments(student_id) if x["status"] not in {"completed", "submitted"}]
            return _personal_response(f"Bạn còn {len(items)} bài tập chưa hoàn thành.", intent, items, student_id)
        if intent == "personal_deadline":
            items = get_upcoming_assignments(student_id)
            return _personal_response(f"Bạn có {len(items)} deadline trong 72 giờ tới.", intent, items, student_id)
        if intent == "personal_exam":
            items = get_exams(student_id)
            return _personal_response(f"Bạn có {len(items)} bài kiểm tra hoặc kỳ thi trong dữ liệu hiện tại.", intent, items, student_id)
        if intent == "personal_announcement":
            items = get_announcements(student_id, unread_only=True)
            return _personal_response(f"Bạn có {len(items)} thông báo chưa đọc.", intent, items, student_id)
        if intent in {"create_note", "create_reminder"}:
            answer = "Mình đã hiểu yêu cầu. Hãy kiểm tra nội dung và xác nhận trước khi lưu."
            response = _personal_response(answer, intent, [], student_id)
            response["requires_confirmation"] = True
            response["confirmation"] = {"action": intent, "raw_message": message}
            return response

    faq = find_faq(message)
    if faq is not None and intent in {"faq", "unknown"}:
        return build_faq_response(faq)

    response = get_mock_response(message)
    response["intent"] = intent
    return response
