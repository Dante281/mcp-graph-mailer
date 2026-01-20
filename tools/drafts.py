import time
import uuid
from typing import Any, Dict, Optional, Tuple


class DraftStore:
    def __init__(self, expiry_seconds: int = 600) -> None:
        # Dict[draft_id, (timestamp, data)]
        self._store: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.expiry_seconds = expiry_seconds

    def create_draft(self, data: Dict[str, Any]) -> str:
        draft_id = str(uuid.uuid4())
        self._store[draft_id] = (time.time(), data)
        return draft_id

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        if draft_id not in self._store:
            return None

        timestamp, data = self._store[draft_id]
        if time.time() - timestamp > self.expiry_seconds:
            # Lazy cleanup on access
            del self._store[draft_id]
            return None

        return data

    def delete_draft(self, draft_id: str) -> None:
        if draft_id in self._store:
            del self._store[draft_id]

    def cleanup(self) -> int:
        """Removes expired drafts and returns count of removed items."""
        now = time.time()
        to_remove = [
            did
            for did, (ts, _) in self._store.items()
            if now - ts > self.expiry_seconds
        ]
        for did in to_remove:
            del self._store[did]
        return len(to_remove)


# Global singleton instance
store = DraftStore()
