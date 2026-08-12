import json
from copy import deepcopy
from pathlib import Path

from repositories.base import DataRepository


ROOT = Path(__file__).resolve().parents[2]


class LocalRepository(DataRepository):
    def __init__(self):
        with (ROOT / "data/sample/faqs.json").open(encoding="utf-8") as stream:
            faqs = json.load(stream)["faqs"]
        with (ROOT / "data/sample/student_context.json").open(encoding="utf-8") as stream:
            personal = json.load(stream)
        with (ROOT / "data/sample/documents.json").open(encoding="utf-8") as stream:
            documents = json.load(stream)["documents"]
        self._seed = {"faqs": faqs, "documents": documents, **{k: v for k, v in personal.items() if isinstance(v, list)}}
        self._runtime = {"notes": [], "reminders": [], "conversations": [], "feedback": []}

    def _collection(self, name):
        if name in self._runtime:
            return self._runtime[name]
        if name not in self._seed:
            raise KeyError(f"Unknown local collection: {name}")
        return self._seed[name]

    def list(self, collection, **filters):
        items = self._collection(collection)
        return [deepcopy(item) for item in items if all(item.get(key) == value for key, value in filters.items())]

    def get(self, collection, item_id):
        item = next((item for item in self._collection(collection) if item.get("id") == item_id), None)
        return deepcopy(item) if item else None

    def upsert(self, collection, item):
        items = self._collection(collection)
        stored = deepcopy(item)
        index = next((i for i, current in enumerate(items) if current.get("id") == stored.get("id")), None)
        if index is None:
            items.append(stored)
        else:
            items[index] = stored
        return deepcopy(stored)

    def clear_runtime(self):
        for items in self._runtime.values():
            items.clear()
