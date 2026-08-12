from abc import ABC, abstractmethod


class DataRepository(ABC):
    @abstractmethod
    def list(self, collection, **filters): ...

    @abstractmethod
    def get(self, collection, item_id): ...

    @abstractmethod
    def upsert(self, collection, item): ...

    @abstractmethod
    def clear_runtime(self): ...
