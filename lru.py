from collections import OrderedDict
from typing import Optional, Tuple, List, Dict, Any

class LRUCache:
    def __init__(self, cap: int) -> None:
        self.capacity: int = cap
        self.cache: OrderedDict[str, str] = OrderedDict()
        self.dirty: Dict[str, bool] = {}

    def get(self, k: str) -> Tuple[Optional[str], str]:
        if k in self.cache:
            self.cache.move_to_end(k)
            return self.cache[k], "HIT"
        return None, "MISS"

    def put(self, k: str, v: str) -> Tuple[Optional[str], Optional[str], bool]:
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
            self.cache[k] = v

        self.dirty[k] = True
        return ek, ev, was_dirty

    def load(self, k: str, v: str) -> Tuple[Optional[str], Optional[str], bool]:
        ek: Optional[str] = None
        ev: Optional[str] = None
        was_dirty: bool = False
        
        if len(self.cache) >= self.capacity:
            ek, ev = self.cache.popitem(last=False)
            was_dirty = self.dirty.pop(ek, False)
        self.cache[k] = v
        self.dirty[k] = False
        return ek, ev, was_dirty

    def get_state(self) -> List[Optional[Dict[str, Any]]]:
        items = list(self.cache.items())
        res: List[Optional[Dict[str, Any]]] = []
        for i in range(self.capacity):
            if i < len(items):
                k, v = items[i]
                is_dirty = self.dirty.get(k, False)
                res.append({"key": k, "data": v, "dirty": is_dirty})
            else:
                res.append(None)
        return res

    def reset(self) -> None:
        self.cache.clear()
        self.dirty.clear()

    def __len__(self) -> int:
        return len(self.cache)
