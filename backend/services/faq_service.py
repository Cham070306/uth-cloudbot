from repositories import get_repository
from services.intent_service import normalize_text


# A single generic token such as "học" or "thi" scores at most 0.5 and must
# not turn schedule/knowledge questions into an unrelated FAQ response.
MIN_SCORE = 0.55
STOP_WORDS = {
    "ai", "cach", "cho", "co", "cua", "dau", "duoc", "gi", "ho", "la", "lam",
    "minh", "nao", "nhu", "o", "ra", "sinh", "the", "theo", "thong", "tin",
    "toi", "tra", "tro", "cuu", "va", "vien", "xem",
}


def load_faqs():
    records = get_repository().list("faqs")
    if not isinstance(records, list):
        raise ValueError("faqs.json must contain a 'faqs' array")
    return records


def searchable_question_count():
    """Count base questions and supported natural-language formulations."""
    return sum(2 + len(faq.get("keywords", [])) for faq in load_faqs())


def _tokens(value):
    return {token for token in normalize_text(value).split() if token not in STOP_WORDS}


def _score(message, faq):
    message_normalized = normalize_text(message)
    message_tokens = _tokens(message)
    terms = [faq["question"], *faq.get("keywords", [])]
    best = 0.0
    for term in terms:
        term_normalized = normalize_text(term)
        term_tokens = _tokens(term)
        if not term_tokens:
            continue
        overlap = len(message_tokens & term_tokens) / len(term_tokens)
        phrase_bonus = 0.35 if term_normalized in message_normalized else 0.0
        best = max(best, min(1.0, overlap + phrase_bonus))
    return best


def find_faq(message):
    message_normalized = normalize_text(message)
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
