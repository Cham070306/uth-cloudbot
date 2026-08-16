from repositories import get_repository
from services.intent_service import normalize_text


# A single generic token such as "học" or "thi" scores at most 0.5 and must
# not turn schedule/knowledge questions into an unrelated FAQ response.
MIN_SCORE = 0.6
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
            overlap = len(message_tokens & term_tokens) / len(term_tokens)
            score = overlap * 0.68
        if score > 0:
            matches.append(score)
    if not matches:
        return 0.0
    # Several matching formulations reinforce the best match without letting
    # many weak generic terms outweigh one precise phrase.
    return min(1.0, max(matches) + min(0.06, 0.015 * (len(matches) - 1)))


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
