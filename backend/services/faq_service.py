from difflib import SequenceMatcher

from repositories import get_repository
from services.intent_service import normalize_text


# A single generic token such as "học" or "thi" scores at most 0.5 and must
# not turn schedule/knowledge questions into an unrelated FAQ response.
MIN_SCORE = 0.6
STOP_WORDS = {
    "ai", "biet", "cach", "can", "cho", "co", "cua", "dau", "duoc", "gi", "ho",
    "hoi", "khong", "la", "lam", "minh", "muon", "nao", "nhu", "o", "ra", "sinh",
    "the", "theo", "thong", "tin", "toi", "tra", "tro", "cuu", "va", "ve", "vien",
    "xem", "xin",
}

# Cách viết thường gặp khi sinh viên chat nhanh. Chỉ áp dụng cho truy hồi FAQ,
# không làm thay đổi bộ phân loại intent cá nhân.
QUERY_ALIASES = {
    "bhyt": "bao hiem y te",
    "dkhp": "dang ky hoc phan",
    "email sv": "email sinh vien",
    "hphi": "hoc phi",
    "ktx": "ky tuc xa",
    "mk": "mat khau",
    "sv": "sinh vien",
    "tkb": "thoi khoa bieu",
}


def load_faqs():
    records = get_repository().list("faqs")
    if not isinstance(records, list):
        raise ValueError("faqs.json must contain a 'faqs' array")
    return records


def searchable_question_count():
    """Count base questions and supported natural-language formulations."""
    return sum(2 + len(faq.get("keywords", [])) for faq in load_faqs())


def _normalize_query(value):
    normalized = normalize_text(value)
    tokens = normalized.split()
    expanded = []
    index = 0
    while index < len(tokens):
        pair = " ".join(tokens[index:index + 2])
        if pair in QUERY_ALIASES:
            expanded.extend(QUERY_ALIASES[pair].split())
            index += 2
            continue
        expanded.extend(QUERY_ALIASES.get(tokens[index], tokens[index]).split())
        index += 1
    return " ".join(expanded)


def _tokens(value, *, is_query=False):
    normalized = _normalize_query(value) if is_query else normalize_text(value)
    return {token for token in normalized.split() if token not in STOP_WORDS}


def _tokens_match(message_token, term_token):
    if message_token == term_token:
        return True
    # Không fuzzy-match từ ngắn vì chúng dễ tạo false positive (thi, hoc, mon...).
    if min(len(message_token), len(term_token)) < 4:
        return False
    return SequenceMatcher(None, message_token, term_token).ratio() >= 0.82


def _fuzzy_coverage(message_tokens, term_tokens):
    if not term_tokens:
        return 0.0
    matched = sum(
        any(_tokens_match(message_token, term_token) for message_token in message_tokens)
        for term_token in term_tokens
    )
    return matched / len(term_tokens)


def _score(message, faq):
    message_normalized = _normalize_query(message)
    message_tokens = _tokens(message, is_query=True)
    terms = [faq["question"], *faq.get("keywords", [])]
    matches = []
    for term in terms:
        term_normalized = normalize_text(term)
        term_tokens = _tokens(term)
        # An exact phrase match outranks token-only overlap. Specific phrases
        # receive a small length bonus, preventing a shorter substring from
        # tying with the intended longer formulation.
        if term_normalized in message_normalized:
            score = min(0.99, 0.72 + min(0.24, len(term_normalized.split()) * 0.04))
        else:
            if not term_tokens:
                continue
            overlap = _fuzzy_coverage(message_tokens, term_tokens)
            score = overlap * 0.68
        if score > 0:
            matches.append(score)
    if not matches:
        return 0.0
    # Several matching formulations reinforce the best match without letting
    # many weak generic terms outweigh one precise phrase.
    return min(1.0, max(matches) + min(0.06, 0.015 * (len(matches) - 1)))


def find_faq(message):
    message_normalized = _normalize_query(message)
    faqs = load_faqs()
    for faq in faqs:
        terms = [faq["question"], *faq.get("keywords", [])]
        if any(normalize_text(term) == message_normalized for term in terms):
            return faq

    ranked = sorted(
        ((_score(message, faq), faq) for faq in faqs),
        key=lambda item: item[0],
        reverse=True,
    )
    if not ranked or ranked[0][0] < MIN_SCORE:
        return None
    return ranked[0][1]


def build_faq_response(faq):
    source = faq["source"]
    return {
        "answer": faq["answer"],
        "intent": "faq",
        "source": source,
        "updated_at": faq.get("updated_at"),
        "invalid": False,
        "paragraphs": [faq["answer"]],
        "list": [],
        "sources": [{"label": source["title"], "url": source.get("url")}],
        "data": {"items": []},
        "ai_generated": False,
        "fallback_used": False,
    }
