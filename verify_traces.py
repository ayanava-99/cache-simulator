from parser import parse_trace
from engine import run_simulation, HardwareCache

# ===== SPATIAL LOCALITY =====
trace = open('traces/spatial_locality.txt').read()
ops = parse_trace(trace)
h = run_simulation(ops, 16, 16, 4, 4, 'Write-Through', 10, 100, 100)
print('=== SPATIAL LOCALITY (addr=16, cache=16, block=4, ways=4) ===')
for s in h:
    step = s["step"]
    raw = s["raw"]
    msg = s["lru"]["msg"]
    print(f'  Step {step}: {raw:20s} -> LRU: {msg}')
final = h[-1]["lru"]
print(f'  Final: hits={final["hits"]}, misses={final["misses"]}')
print()

# ===== THRASHING direct-mapped =====
trace = open('traces/thrashing.txt').read()
ops = parse_trace(trace)
h = run_simulation(ops, 16, 8, 4, 1, 'Write-Through', 10, 100, 100)
ns, ob, ib, tb = HardwareCache.calc_bits(16, 8, 4, 1)
print(f'=== THRASHING (addr=16, cache=8, block=4, ways=1) sets={ns} ===')
for s in h:
    bd = s['breakdown']
    step = s["step"]
    raw = s["raw"]
    msg = s["lru"]["msg"]
    print(f'  Step {step}: {raw:20s} -> idx={bd["index"]} tag={bd["tag"]} -> LRU: {msg}')
final = h[-1]["lru"]
print(f'  Final: hits={final["hits"]}, misses={final["misses"]}')
print()

# Thrashing fix with ways=2
h2 = run_simulation(ops, 16, 8, 4, 2, 'Write-Through', 10, 100, 100)
ns2, _, _, _ = HardwareCache.calc_bits(16, 8, 4, 2)
print(f'=== THRASHING FIX (addr=16, cache=8, block=4, ways=2) sets={ns2} ===')
for s in h2:
    bd = s['breakdown']
    step = s["step"]
    raw = s["raw"]
    msg = s["lru"]["msg"]
    print(f'  Step {step}: {raw:20s} -> idx={bd["index"]} tag={bd["tag"]} -> LRU: {msg}')
final = h2[-1]["lru"]
print(f'  Final: hits={final["hits"]}, misses={final["misses"]}')
print()

# ===== BELADY =====
trace = open('traces/beladys_anomaly.txt').read()
ops = parse_trace(trace)
h3 = run_simulation(ops, 16, 12, 4, 3, 'Write-Through', 10, 100, 100)
h4 = run_simulation(ops, 16, 16, 4, 4, 'Write-Through', 10, 100, 100)
ns3, _, _, _ = HardwareCache.calc_bits(16, 12, 4, 3)
ns4, _, _, _ = HardwareCache.calc_bits(16, 16, 4, 4)
print(f'=== BELADY ways=3 (cache=12, sets={ns3}) ===')
print(f'  FIFO misses: {h3[-1]["fifo"]["misses"]}, LRU misses: {h3[-1]["lru"]["misses"]}')
print(f'=== BELADY ways=4 (cache=16, sets={ns4}) ===')
print(f'  FIFO misses: {h4[-1]["fifo"]["misses"]}, LRU misses: {h4[-1]["lru"]["misses"]}')
print()

# ===== WRITE-BACK =====
trace = open('traces/write_back_demo.txt').read()
ops = parse_trace(trace)
h = run_simulation(ops, 16, 8, 4, 1, 'Write-Back', 10, 100, 100)
ns, _, _, _ = HardwareCache.calc_bits(16, 8, 4, 1)
print(f'=== WRITE-BACK (addr=16, cache=8, block=4, ways=1, WB) sets={ns} ===')
for s in h:
    bd = s['breakdown']
    step = s["step"]
    raw = s["raw"]
    msg = s["lru"]["msg"]
    db_msg = s["lru"]["db_msg"] or "-"
    db_state = s["lru"]["db_state"]
    print(f'  Step {step}: {raw:30s} -> idx={bd["index"]} -> LRU: {msg}')
    print(f'    DB msg: {db_msg}')
    print(f'    DB state: {db_state}')
print()

# ===== DIVERGENCE =====
trace = open('traces/divergence.txt').read()
ops = parse_trace(trace)
h = run_simulation(ops, 16, 8, 4, 2, 'Write-Through', 10, 100, 100)
ns, _, _, _ = HardwareCache.calc_bits(16, 8, 4, 2)
print(f'=== DIVERGENCE (addr=16, cache=8, block=4, ways=2) sets={ns} ===')
for s in h:
    step = s["step"]
    raw = s["raw"]
    lru_msg = s["lru"]["msg"]
    fifo_msg = s["fifo"]["msg"]
    print(f'  Step {step}: {raw:20s} -> LRU: {lru_msg:50s} | FIFO: {fifo_msg}')
lru_m = h[-1]["lru"]["misses"]
fifo_m = h[-1]["fifo"]["misses"]
print(f'  LRU misses={lru_m}, FIFO misses={fifo_m}')
