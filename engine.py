from lru import LRUCache
from fifo import FIFOCache
from database import SlowDatabase
import copy
import math
from typing import List, Dict, Any, Tuple, Optional

class HardwareCache:
    def __init__(self, address_bits: int, cache_size: int, block_size: int, ways: int, policy: str):
        self.address_bits = address_bits
        self.cache_size = cache_size
        self.block_size = block_size
        self.ways = ways
        self.num_sets = cache_size // (block_size * ways)
        
        self.offset_bits = int(math.log2(block_size))
        self.index_bits = int(math.log2(self.num_sets))
        self.tag_bits = address_bits - self.index_bits - self.offset_bits
        
        if policy.lower() == "lru":
            self.sets = [LRUCache(ways) for _ in range(self.num_sets)]
        else:
            self.sets = [FIFOCache(ways) for _ in range(self.num_sets)]
            
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _extract(self, addr_val: int) -> Tuple[int, int, int]:
        offset = addr_val & ((1 << self.offset_bits) - 1)
        index = (addr_val >> self.offset_bits) & ((1 << self.index_bits) - 1)
        tag = addr_val >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    def _format_hex(self, val: int, bits: int) -> str:
        hex_chars = max(1, (bits + 3) // 4)
        return f"0x{val:0{hex_chars}X}"
        
    def _reconstruct_addr(self, tag_val: int, index: int) -> str:
        addr_val = (tag_val << (self.index_bits + self.offset_bits)) | (index << self.offset_bits)
        return self._format_hex(addr_val, self.address_bits)

    def get(self, addr_val: int) -> Tuple[Optional[str], str, Dict[str, Any]]:
        tag, index, offset = self._extract(addr_val)
        tag_hex = self._format_hex(tag, self.tag_bits)
        
        val, status = self.sets[index].get(tag_hex)
        if status == "HIT":
            self.hits += 1
        else:
            self.misses += 1
            
        breakdown = {"tag": tag_hex, "index": index, "offset": offset}
        return val, status, breakdown

    def put(self, addr_val: int, v: str) -> Tuple[Optional[str], Optional[str], bool, Dict[str, Any]]:
        tag, index, offset = self._extract(addr_val)
        tag_hex = self._format_hex(tag, self.tag_bits)
        
        ek_tag, ev, was_dirty = self.sets[index].put(tag_hex, v)
        
        ek_addr = None
        if ek_tag:
            self.evictions += 1
            ek_tag_val = int(ek_tag, 16)
            ek_addr = self._reconstruct_addr(ek_tag_val, index)
            
        breakdown = {"tag": tag_hex, "index": index, "offset": offset}
        return ek_addr, ev, was_dirty, breakdown

    def load(self, addr_val: int, v: str) -> Tuple[Optional[str], Optional[str], bool, Dict[str, Any]]:
        tag, index, offset = self._extract(addr_val)
        tag_hex = self._format_hex(tag, self.tag_bits)
        
        ek_tag, ev, was_dirty = self.sets[index].load(tag_hex, v)
        
        ek_addr = None
        if ek_tag:
            self.evictions += 1
            ek_tag_val = int(ek_tag, 16)
            ek_addr = self._reconstruct_addr(ek_tag_val, index)
            
        breakdown = {"tag": tag_hex, "index": index, "offset": offset}
        return ek_addr, ev, was_dirty, breakdown
        
    def get_state(self) -> List[List[Optional[Dict[str, Any]]]]:
        return [s.get_state() for s in self.sets]

def run_simulation(ops: List[Dict[str, Any]], address_bits: int, cache_size: int, block_size: int, ways: int, mode: str, hit_t: int, read_t: int, write_t: int, dirty_pct: float = 0.0) -> List[Dict[str, Any]]:
    lru = HardwareCache(address_bits, cache_size, block_size, ways, "lru")
    fifo = HardwareCache(address_bits, cache_size, block_size, ways, "fifo")
    
    db_lru = SlowDatabase()
    db_fifo = SlowDatabase()
    
    # We don't pre-seed anymore because addresses are large hex strings.
    # The database starts empty.
    
    history: List[Dict[str, Any]] = []
    
    for i, op in enumerate(ops):
        addr_hex = op["addr_hex"]
        addr_val = op["addr_val"]
        
        def process_op(cache: HardwareCache, db: SlowDatabase) -> Tuple[str, str, Dict[str, Any]]:
            evict_addr = None
            db_msg = None
            breakdown = None
            
            # Helper to block-align addresses for DB interaction
            tag, index, _ = cache._extract(addr_val)
            block_addr = cache._reconstruct_addr(tag, index)
            
            if op["op"] == "W":
                v = op["val"]
                evict_addr, evict_v, was_dirty, breakdown = cache.put(addr_val, v)
                
                if mode == "Write-Through":
                    t = hit_t + write_t
                    db.data[block_addr] = v
                    msg = f"WRITE {addr_hex} v={v} | {t} ms"
                    db_msg = f"DB UPDATED (Write-Through): {block_addr} = {v}"
                else:
                    t = hit_t
                    if evict_addr and was_dirty:
                        wt = t + write_t
                        db.data[evict_addr] = evict_v
                        t = wt
                        db_msg = f"DB UPDATED (Write-Back Eviction): {evict_addr} = {evict_v}"
                    msg = f"WRITE {addr_hex} v={v} | {t} ms"
                    
                if evict_addr:
                    msg += f" | EVICT {evict_addr}"
                    
                return msg, db_msg, breakdown
                
            else:
                val, res, breakdown = cache.get(addr_val)
                if res == "HIT":
                    t = hit_t
                    msg = f"READ {addr_hex} | HIT | {t} ms"
                else:
                    db_val = db.data.get(block_addr, f"data_{block_addr}")
                    evict_addr, evict_v, was_dirty, breakdown = cache.load(addr_val, db_val)
                    t = hit_t + read_t + hit_t
                    if mode == "Write-Back" and evict_addr and was_dirty:
                        db.data[evict_addr] = evict_v
                        t += write_t
                        db_msg = f"DB UPDATED (Write-Back Eviction): {evict_addr} = {evict_v}"
                    msg = f"READ {addr_hex} | MISS | {t} ms"
                        
                if evict_addr:
                    msg += f" | EVICT {evict_addr}"
                return msg, db_msg, breakdown

        lru_msg, lru_db_msg, breakdown = process_op(lru, db_lru)
        fifo_msg, fifo_db_msg, _ = process_op(fifo, db_fifo)
        
        def compute_emat(cache: HardwareCache) -> Tuple[float, str]:
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

        snapshot: Dict[str, Any] = {
            "step": i + 1,
            "raw": op["raw"],
            "breakdown": breakdown,
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
