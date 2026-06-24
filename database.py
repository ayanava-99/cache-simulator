from typing import Dict, Any

class SlowDatabase:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}

    def seed(self, entries: Dict[str, Any]) -> None:
        self.data.update(entries)
