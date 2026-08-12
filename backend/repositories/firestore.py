from repositories.base import DataRepository


class FirestoreRepository(DataRepository):
    """Firestore adapter loaded only when DATA_BACKEND=firestore."""

    def __init__(self, project=None, prefix="uth_cloudbot"):
        try:
            from google.cloud import firestore
        except ImportError as error:
            raise RuntimeError("DATA_BACKEND=firestore requires package google-cloud-firestore.") from error
        try:
            self.client = firestore.Client(project=project)
        except Exception as error:
            raise RuntimeError("Cannot initialize Firestore. Check GOOGLE_CLOUD_PROJECT and Application Default Credentials.") from error
        self.prefix = prefix

    def _ref(self, collection):
        return self.client.collection(f"{self.prefix}_{collection}")

    def list(self, collection, **filters):
        query = self._ref(collection)
        for key, value in filters.items():
            query = query.where(key, "==", value)
        return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()]

    def get(self, collection, item_id):
        snapshot = self._ref(collection).document(item_id).get()
        return {"id": snapshot.id, **snapshot.to_dict()} if snapshot.exists else None

    def upsert(self, collection, item):
        stored = dict(item)
        item_id = stored.pop("id")
        self._ref(collection).document(item_id).set(stored, merge=True)
        return {"id": item_id, **stored}

    def clear_runtime(self):
        raise RuntimeError("clear_runtime is available only for the local test repository.")
