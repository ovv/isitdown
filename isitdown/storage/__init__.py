import logging
from collections import defaultdict

LOG = logging.getLogger(__name__)


class BaseStorage:
    def __init__(self):
        pass

    async def save(self, result):
        pass

    async def fetch(self, check_name, count=1):
        pass


class MemoryStorage(BaseStorage):
    def __init__(self, max_items=5):
        self.max_items = max_items
        self._store = defaultdict(list)

    async def save(self, result):
        self._store[result.check].append(result)

        if self.max_items and len(self._store[result.check]) > self.max_items:
            del self._store[result.check][0]

    async def fetch(self, check_name, count=1):
        if count:
            return self._store[check_name][-count:]
        else:
            return self._store[check_name]
