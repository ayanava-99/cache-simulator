from parser import parse_trace
from engine import run_simulation

trace = open('traces/divergence.txt').read()
ops = parse_trace(trace)
h = run_simulation(ops, 16, 8, 4, 2, 'Write-Through', 10, 100, 100)
print('=== NEW DIVERGENCE (16/8/4/2) ===')
for s in h:
    step = s['step']
    raw = s['raw']
    lm = s['lru']['msg']
    fm = s['fifo']['msg']
    print(f'  Step {step}: {raw:15s} LRU: {lm:50s} FIFO: {fm}')
lru_m = h[-1]["lru"]["misses"]
fifo_m = h[-1]["fifo"]["misses"]
print(f'  LRU misses={lru_m}, FIFO misses={fifo_m}')
