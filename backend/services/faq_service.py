import json
from functools import lru_cache
from pathlib import Path

from services.intent_service import normalize_text


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample" / "faqs.json"
MIN_SCORE = 0.45
STOP_WORDS = {
    "ai", "cach", "cho", "co", "cua", "dau", "duoc", "gi", "ho", "la", "lam",
    "minh", "nao", "nhu", "o", "ra", "sinh", "the", "theo", "thong", "tin",
    "toi", "tra", "tro", "cuu", "va", "vien", "xem",
}


@lru_cache(maxsize=1)
def load_faqs():
    with DATA_PATH.open(encoding="utf-8") as data_file:
        payload = json.load(data_file)
    records = payload.get("faqs")
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
    ranked = sorted(
        ((_score(message, faq), faq) for faq in load_faqs()),
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
    }
