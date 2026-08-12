import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_repository():
    backend = os.getenv("DATA_BACKEND", "local").strip().lower()
    if backend == "local":
        from repositories.local import LocalRepository
        return LocalRepository()
    if backend == "firestore":
        from repositories.firestore import FirestoreRepository
        return FirestoreRepository(os.getenv("GOOGLE_CLOUD_PROJECT"), os.getenv("FIRESTORE_COLLECTION_PREFIX", "uth_cloudbot"))
    raise RuntimeError("DATA_BACKEND must be 'local' or 'firestore'.")


def reset_repository_cache():
    get_repository.cache_clear()
