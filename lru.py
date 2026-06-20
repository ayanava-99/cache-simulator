from collections import OrderedDict
from typing import Optional, Tuple, List, Dict, Any

class LRUCache:
    """Least Recently Used (LRU) Cache policy simulator.
    
    This class tracks the cache state, including the items, their dirty bits,
    and performance statistics (hits, misses, evictions). It uses an OrderedDict
    to efficiently maintain the MRU/LRU order.
    """
    
    def __init__(self, cap: int) -> None:
        """Initialize the LRU Cache.
        
        Args:
            cap: Maximum number of items the cache can hold.
        """
        self.capacity: int = cap
        self.cache: OrderedDict[str, str] = OrderedDict()
        self.dirty: Dict[str, bool] = {}
        self.hits: int = 0
        self.misses: int = 0
        self.evictions: int = 0

    def get(self, k: str) -> Tuple[Optional[str], str]:
        """Attempt to retrieve an item from the cache.
        
        Args:
            k: The key to look up.
            
        Returns:
            A tuple of (value, status) where status is 'HIT' or 'MISS'.
            If missed, value is None.
        """
        if k in self.cache:
            self.cache.move_to_end(k)
            self.hits += 1
            return self.cache[k], "HIT"
        self.misses += 1
        return None, "MISS"

    def put(self, k: str, v: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Write an item to the cache, marking it as dirty.
        
        Args:
            k: The key to write.
            v: The value to write.
            
        Returns:
            A tuple of (evicted_key, evicted_value, was_dirty) if an eviction
            occurred, otherwise (None, None, False).
        """
        ek: Optional[str] = None
        ev: Optional[str] = None
        was_dirty: bool = False

        if k in self.cache:
            self.cache.move_to_end(k)
            self.cache[k] = v
        else:
            if len(self.cache) >= self.capacity:
                ek, ev = self.cache.popitem(last=False)
                was_dirty = self.dirty.pop(ek, False)
                self.evictions += 1
            self.cache[k] = v

        self.dirty[k] = True
        return ek, ev, was_dirty

    def load(self, k: str, v: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Load an item into the cache from the database (not dirty).
        
        Args:
            k: The key to load.
            v: The value retrieved from the database.
            
        Returns:
            A tuple of (evicted_key, evicted_value, was_dirty) if an eviction
            occurred, otherwise (None, None, False).
        """
        ek: Optional[str] = None
        ev: Optional[str] = None
        was_dirty: bool = False
        
        if len(self.cache) >= self.capacity:
            ek, ev = self.cache.popitem(last=False)
            was_dirty = self.dirty.pop(ek, False)
            self.evictions += 1
        self.cache[k] = v
        self.dirty[k] = False
        return ek, ev, was_dirty

    def get_state(self) -> List[Optional[Dict[str, Any]]]:
        """Return the current state of the cache for visualization.
        
        Returns:
            A list of length `self.capacity`. Empty slots are `None`.
            Filled slots are dicts with 'tag', 'dirty', 'data'.
        """
        items = list(self.cache.items())
        res: List[Optional[Dict[str, Any]]] = []
        for i in range(self.capacity):
            if i < len(items):
                k, v = items[i]
                is_dirty = self.dirty.get(k, False)
                res.append({"tag": k, "data": v, "dirty": is_dirty})
            else:
                res.append(None)
        return res

    def hit_rate(self) -> float:
        """Calculate the cache hit rate.
        
        Returns:
            The hit rate as a percentage (0.0 to 100.0).
        """
        t = self.hits + self.misses
        if t > 0:
            return (self.hits / t) * 100.0
        return 0.0

    def reset(self) -> None:
        """Clear the cache and reset all statistics."""
        self.cache.clear()
        self.dirty.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def __len__(self) -> int:
        """Return the number of items currently in the cache."""
        return len(self.cache)
