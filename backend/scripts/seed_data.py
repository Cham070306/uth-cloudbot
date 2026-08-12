"""Idempotently copy bundled local demo data into the configured repository."""
from repositories import get_repository
from repositories.local import LocalRepository


COLLECTIONS = ("faqs", "documents", "students", "schedules", "assignments", "exams", "announcements")


def seed(repository=None, source=None):
    repository = repository or get_repository()
    source = source or LocalRepository()
    counts = {}
    for collection in COLLECTIONS:
        items = source.list(collection)
        for item in items:
            repository.upsert(collection, item)
        counts[collection] = len(items)
    return counts


if __name__ == "__main__":
    print(seed())
