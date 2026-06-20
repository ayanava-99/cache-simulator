from lru import LRUCache
from fifo import FIFOCache
from database import SlowDatabase
import copy

def run_simulation(ops, capacity, mode, hit_t, read_t, write_t, dirty_pct=0.0):
    lru = LRUCache(capacity)
    fifo = FIFOCache(capacity)
    
    db_lru = SlowDatabase()
    db_fifo = SlowDatabase()
    
    seed_data = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "F", "7": "G", "8": "H", "9": "I", "10": "J"}
    db_lru.seed(copy.deepcopy(seed_data))
    db_fifo.seed(copy.deepcopy(seed_data))
    
    history = []
    
    for i, op in enumerate(ops):
        k = str(op["key"])
        
        def process_op(cache, db):
            evict_k = None
            db_msg = None
            if op["op"] == "W":
                v = op["val"]
                evict_k, evict_v, was_dirty = cache.put(k, v)
                
                if mode == "Write-Through":
                    t = hit_t + write_t
                    db.data[k] = v
                    msg = f"WRITE k={k} v={v} | {t} ms"
                    db_msg = f"DB UPDATED (Write-Through): k={k} v={v}"
                else:
                    t = hit_t
                    if evict_k and was_dirty:
                        wt = t + write_t
                        db.data[evict_k] = evict_v
                        t = wt
                        db_msg = f"DB UPDATED (Write-Back Eviction): k={evict_k} v={evict_v}"
                    msg = f"WRITE k={k} v={v} | {t} ms"
                    
                if evict_k:
                    msg += f" | EVICT {evict_k}"
                    
                return msg, db_msg
                
            else:
                val, res = cache.get(k)
                if res == "HIT":
                    t = hit_t
                    msg = f"READ k={k} | HIT | {t} ms"
                else:
                    db_val = db.data.get(k, None)
                    if db_val is not None:
                        evict_k, evict_v, was_dirty = cache.load(k, db_val)
                        t = hit_t + read_t + hit_t
                        if mode == "Write-Back" and evict_k and was_dirty:
                            db.data[evict_k] = evict_v
                            t += write_t
                            db_msg = f"DB UPDATED (Write-Back Eviction): k={evict_k} v={evict_v}"
                        msg = f"READ k={k} | MISS | {t} ms"
                    else:
                        t = hit_t + read_t
                        msg = f"READ k={k} | NOT FOUND | {t} ms"
                        evict_k = None
                        
                if evict_k:
                    msg += f" | EVICT {evict_k}"
                return msg, db_msg

        lru_msg, lru_db_msg = process_op(lru, db_lru)
        fifo_msg, fifo_db_msg = process_op(fifo, db_fifo)
        
        def compute_emat(cache):
            tot = cache.hits + cache.misses
            if tot == 0: return 0.0, "N/A"
            mr = cache.misses / tot
            if mode == "Write-Through":
                emat = hit_t + (mr * read_t)
                calc_str = f"EMAT = T_hit + (MissRate * T_read) = {hit_t} + ({mr:.2f} * {read_t}) = **{emat:.1f} ms**"
                return emat, calc_str
            else:
                emat = hit_t + (mr * (read_t + (dirty_pct * write_t)))
                calc_str = f"EMAT = T_hit + (MissRate * (T_read + (DirtyRate * T_wb))) = {hit_t} + ({mr:.2f} * ({read_t} + ({dirty_pct:.2f} * {write_t}))) = **{emat:.1f} ms**"
                return emat, calc_str
                
        lru_state = lru.get_state()
        fifo_state = fifo.get_state()
        
        lru_emat, lru_emat_str = compute_emat(lru)
        fifo_emat, fifo_emat_str = compute_emat(fifo)
        
        if mode == "Write-Through":
            for item in lru_state: item["Status"] = item["Status"].replace(" *", "")
            for item in fifo_state: item["Status"] = item["Status"].replace(" *", "")

        snapshot = {
            "step": i + 1,
            "raw": op["raw"],
            "lru": {
                "state": lru_state,
                "msg": lru_msg,
                "db_msg": lru_db_msg,
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
