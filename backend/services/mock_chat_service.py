import json
from copy import deepcopy
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "mock_responses.json"


def _load_mock():
    with DATA_PATH.open(encoding="utf-8") as data_file:
        return json.load(data_file)


def get_mock_response(_message):
    record = deepcopy(_load_mock()["default"])
    source = record["source"]
    # Canonical BE-01 fields plus presentation aliases consumed by FE-01.
    record.update({
        "invalid": False,
        "paragraphs": [record["answer"]],
        "list": [],
        "sources": [{"label": source["title"], "url": source["url"]}],
    })
    return record
