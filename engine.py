from lru import LRUCache
from fifo import FIFOCache
from database import SlowDatabase
import copy
from typing import List, Dict, Any, Tuple, Optional

class CacheSimWrapper:
    def __init__(self, cache_size: int, policy: str):
        self.cache_size=cache_size
        if policy.lower()=="lru":
            self.cache= LRUCache(cache_size)
        else:
            self.cache=FIFOCache(cache_size)
            
        self.hits= 0
        self.misses=0
        self.evictions =0

    def get(self, key: str) -> Tuple[Optional[str], str]:
        val, status= self.cache.get(key)
        if status=="HIT":
            self.hits+=1
        else:
            self.misses +=1
        return val, status

    def put(self, key: str, v: str) -> Tuple[Optional[str], Optional[str], bool]:
        ek, ev, was_dirty=self.cache.put(key, v)
        if ek:
            self.evictions+=1
        return ek, ev, was_dirty

    def load(self, key: str, v: str) -> Tuple[Optional[str], Optional[str], bool]:
        ek, ev, was_dirty= self.cache.load(key, v)
        if ek:
            self.evictions+= 1
        return ek, ev, was_dirty
        
    def get_state(self) -> List[Optional[Dict[str, Any]]]:
        return self.cache.get_state()

def run_simulation(ops: List[Dict[str, Any]], cache_size: int, mode: str, hit_t: int, read_t: int, write_t: int, dirty_pct: float = 0.0) -> List[Dict[str, Any]]:
    lru= CacheSimWrapper(cache_size, "lru")
    fifo=CacheSimWrapper(cache_size, "fifo")
    
    db_lru=SlowDatabase()
    db_fifo= SlowDatabase()
    
    unique_keys=set(op["key"] for op in ops)
    for k in unique_keys:
        db_lru.data[k]=f"data_{k}"
        db_fifo.data[k]= f"data_{k}"
    
    history: List[Dict[str, Any]]=[]
    
    history.append({
        "step": 0,
        "raw": "INITIAL STATE",
        "key": "-",
        "lru": {
            "state": lru.get_state(),
            "msg": "Waiting for first request...",
            "db_msg": None,
            "db_updated_key": None,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "amat": 0.0,
            "amat_str": "EMAT: N/A",
            "db_state": copy.deepcopy(db_lru.data)
        },
        "fifo": {
            "state": fifo.get_state(),
            "msg": "Waiting for first request...",
            "db_msg": None,
            "db_updated_key": None,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "amat": 0.0,
            "amat_str": "EMAT: N/A",
            "db_state": copy.deepcopy(db_fifo.data)
        }
    })
    
    for i, op in enumerate(ops):
        key=op["key"]
        
        def process_op(cache: CacheSimWrapper, db: SlowDatabase) -> Tuple[str, str, Optional[str]]:
            db_msg=None
            evict_key= None
            updated_db_key=None
            
            if op["op"]=="W":
                v=op["val"]
                evict_key, evict_v, was_dirty= cache.put(key, v)
                
                if mode=="Write-Through":
                    t=hit_t + write_t
                    db.data[key]=v
                    updated_db_key= key
                    msg=f"WRITE {key} v={v} | {t} ms"
                    db_msg=f"DB UPDATED (Write-Through): {key} = {v}"
                else:
                    t= hit_t
                    if evict_key and was_dirty:
                        wt=t + write_t
                        db.data[evict_key]= evict_v
                        updated_db_key= evict_key
                        t=wt
                        db_msg=f"DB UPDATED (Write-Back Eviction): {evict_key} = {evict_v}"
                    msg= f"WRITE {key} v={v} | {t} ms"
                    
                if evict_key:
                    msg+=f" | EVICT {evict_key}"
                    
                return msg, db_msg, updated_db_key
                
            else:
                val, res= cache.get(key)
                if res=="HIT":
                    t= hit_t
                    msg= f"READ {key} | HIT | {t} ms"
                else:
                    db_val=db.data.get(key, f"data_{key}")
                    evict_key, evict_v, was_dirty= cache.load(key, db_val)
                    t= hit_t + read_t + hit_t
                    if mode=="Write-Back" and evict_key and was_dirty:
                        db.data[evict_key]= evict_v
                        updated_db_key= evict_key
                        t+= write_t
                        db_msg= f"DB UPDATED (Write-Back Eviction): {evict_key} = {evict_v}"
                    msg= f"READ {key} | MISS | {t} ms"
                        
                if evict_key:
                    msg+= f" | EVICT {evict_key}"
                return msg, db_msg, updated_db_key

        lru_msg, lru_db_msg, lru_updated_db_key= process_op(lru, db_lru)
        fifo_msg, fifo_db_msg, fifo_updated_db_key=process_op(fifo, db_fifo)
        
        def compute_emat(cache: CacheSimWrapper) -> Tuple[float, str]:
            tot= cache.hits + cache.misses
            if tot==0: return 0.0, "N/A"
            mr= cache.misses / tot
            if mode=="Write-Through":
                emat= hit_t + (mr * (read_t + hit_t))
                calc_str=f"EMAT = T_hit + (MissRate * (T_read + T_hit)) = {hit_t} + ({mr:.2f} * ({read_t} + {hit_t})) = **{emat:.1f} ms**"
                return emat, calc_str
            else:
                emat= hit_t + (mr * (read_t + hit_t + (dirty_pct * write_t)))
                calc_str=f"EMAT = T_hit + (MissRate * (T_read + T_hit + (DirtyRate * T_wb))) = {hit_t} + ({mr:.2f} * ({read_t} + {hit_t} + ({dirty_pct:.2f} * {write_t}))) = **{emat:.1f} ms**"
                return emat, calc_str
                
        lru_state= lru.get_state()
        fifo_state= fifo.get_state()
        
        lru_emat, lru_emat_str= compute_emat(lru)
        fifo_emat, fifo_emat_str= compute_emat(fifo)

        snapshot: Dict[str, Any] = {
            "step": i + 1,
            "raw": op["raw"],
            "key": key,
            "lru": {
                "state": lru_state,
                "msg": lru_msg,
                "db_msg": lru_db_msg,
                "db_updated_key": lru_updated_db_key,
                "hits": lru.hits,
                "misses": lru.misses,
                "evictions": lru.evictions,
                "amat": lru_emat,
                "amat_str": lru_emat_str,
                "db_state": copy.deepcopy(db_lru.data)
            },
            "fifo": {
                "state": fifo_state,
                "msg": fifo_msg,
                "db_msg": fifo_db_msg,
                "db_updated_key": fifo_updated_db_key,
                "hits": fifo.hits,
                "misses": fifo.misses,
                "evictions": fifo.evictions,
                "amat": fifo_emat,
                "amat_str": fifo_emat_str,
                "db_state": copy.deepcopy(db_fifo.data)
            }
        }
        history.append(snapshot)
        
    return history
