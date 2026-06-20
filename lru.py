from collections import OrderedDict

class LRUCache:
    def __init__(self, cap):
        self.capacity = cap
        self.cache =OrderedDict()
        self.dirty= {}
        self.hits =0
        self.misses = 0
        self.evictions = 0

    def get(self, k):
        if k in self.cache:
            self.cache.move_to_end(k)
            self.hits += 1
            return self.cache[k],"HIT"
        self.misses += 1
        return None,"MISS"

    def put(self, k, v):
        ek = None
        ev = None
        was_dirty = False


        if k in self.cache:
            self.cache.move_to_end(k)
            self.cache[k] = v
        else:

            if len(self.cache) >= self.capacity:
                ek, ev = self.cache.popitem(last=False)
                was_dirty = self.dirty.pop(ek, False)
                self.evictions += 1
            self.cache[k]= v

        self.dirty[k] = True
        return ek,ev,was_dirty

    def load(self, k, v):
        ev,ek =None, None
        was_dirty = False
        if len(self.cache) >= self.capacity:
            ek, ev = self.cache.popitem(last=False)
            was_dirty =self.dirty.pop(ek, False)
            self.evictions +=1
        self.cache[k]= v
        self.dirty[k] = False
        return ek, ev, was_dirty

    def get_state(self):
        items = list(self.cache.items())
        res = []
        for i, (k, v) in enumerate(items):
            stat = ""
            if len(items)>1 and i== 0:
                stat= "LRU"
            if i== len(items) - 1:
                stat = "MRU"
            is_dirty = self.dirty.get(k, False)
            res.append({"Position": i + 1, "Key": k, "Value": v, "Status": stat, "IsDirty": is_dirty})
        return res

    def hit_rate(self):
        t = self.hits + self.misses
        if t > 0:
            return (self.hits/t) *100
        return 0.0

    def reset(self):
        self.cache.clear()
        self.dirty.clear()
        self.hits =0
        self.misses=0
        self.evictions= 0

    def __len__(self):
        return len(self.cache)
