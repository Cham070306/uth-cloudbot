import re
import unicodedata


INTENT_KEYWORDS = {
    "create_reminder": ("nhac toi", "nhac minh", "tao nhac nho"),
    "create_note": ("ghi chu", "luu ghi chu", "note lai"),
    "personal_deadline": ("deadline", "sap het han", "gan het han", "qua han"),
    "personal_assignment": ("bai tap", "e learning", "chua lam", "chua nop"),
    "personal_announcement": ("thong bao moi", "thong bao chua doc"),
    "personal_exam": ("toi co kiem tra", "co bai kiem tra", "kiem tra tuan"),
    "personal_schedule": ("toi hoc", "minh hoc", "hoc mon gi", "lich cua toi", "lich cua minh"),
    "exam_schedule": ("lich thi", "thi cuoi ky", "thi giua ky", "phong thi", "ca thi"),
    "schedule": ("lich hoc", "thoi khoa bieu", "phong hoc", "ca hoc", "hoc bu"),
    "document": ("tai lieu", "giao trinh", "de cuong", "slide", "bai giang"),
    "knowledge": ("giai thich", "khai niem", "la gi", "tai sao", "nhu the nao"),
}

FAQ_KEYWORDS = (
    "hoc phi", "dang ky hoc phan", "rut hoc phan", "bao luu", "hoc bong",
    "email sinh vien", "wifi", "thu vien", "the sinh vien", "phong dao tao",
    "cong tac sinh vien", "tot nghiep", "bang diem", "phuc khao", "nghi hoc",
)


def normalize_text(value):
    value = unicodedata.normalize("NFD", value.casefold())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = value.replace("đ", "d")
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    return re.sub(r"\bdang ki\b", "dang ky", value)


def classify_intent(message):
    normalized = normalize_text(message)
    def contains(keyword):
        return re.search(rf"(?:^|\s){re.escape(keyword)}(?:$|\s)", normalized) is not None

    priority = (
        "create_reminder", "create_note", "personal_deadline", "personal_assignment",
        "personal_announcement", "personal_exam", "personal_schedule", "exam_schedule", "schedule",
    )
    for intent in priority:
        if any(contains(keyword) for keyword in INTENT_KEYWORDS[intent]):
            return intent
    if any(contains(keyword) for keyword in FAQ_KEYWORDS):
        return "faq"
    for intent in ("document", "knowledge"):
        if any(contains(keyword) for keyword in INTENT_KEYWORDS[intent]):
            return intent
    return "unknown"
