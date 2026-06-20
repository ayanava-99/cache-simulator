from typing import Dict, Any

class SlowDatabase:
    """A simulated slow database backend for the cache simulator.
    
    This class simply stores key-value pairs in a dictionary.
    Performance timings (e.g. read latency, write latency) are
    simulated externally by the engine.
    """
    
    def __init__(self) -> None:
        """Initialize an empty database."""
        self.data: Dict[str, Any] = {}

    def seed(self, entries: Dict[str, Any]) -> None:
        """Populate the database with initial key-value pairs.
        
        Args:
            entries: A dictionary of key-value pairs to insert.
        """
        self.data.update(entries)
