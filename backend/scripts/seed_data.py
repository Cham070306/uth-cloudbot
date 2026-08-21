"""Idempotently copy bundled local demo data into the configured repository."""
import argparse

from repositories import get_repository
from repositories.local import LocalRepository


COLLECTIONS = ("faqs", "documents", "students", "schedules", "assignments", "exams", "announcements")


def seed(repository=None, source=None, collections=None):
    repository = repository or get_repository()
    source = source or LocalRepository()
    selected = tuple(collections or COLLECTIONS)
    unknown = set(selected) - set(COLLECTIONS)
    if unknown:
        raise ValueError(f"Unknown collections: {', '.join(sorted(unknown))}")
    counts = {}
    for collection in selected:
        items = source.list(collection)
        for item in items:
            repository.upsert(collection, item)
        counts[collection] = len(items)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--collection",
        action="append",
        choices=COLLECTIONS,
        dest="collections",
        help="Seed only this collection; repeat the option to select more than one.",
    )
    args = parser.parse_args()
    print(seed(collections=args.collections))
