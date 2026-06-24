import pytest
from engine import run_simulation
from parser import parse_trace

def test_lru_better_than_fifo():
    trace = "R 1\nW 2 B\nR 3\nR 4\nR 1\nR 2\nW 5 C\nR 1\nR 2\nR 3"
    ops = parse_trace(trace)
    
    history = run_simulation(ops, cache_size=4, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    
    lru_misses = history[-1]["lru"]["misses"]
    fifo_misses = history[-1]["fifo"]["misses"]
    
    assert lru_misses < fifo_misses

def test_beladys_anomaly():
    trace = "R 1\nR 2\nR 3\nR 4\nR 1\nR 2\nR 5\nR 1\nR 2\nR 3\nR 4\nR 5"
    ops = parse_trace(trace)
    
    history_3 = run_simulation(ops, cache_size=3, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    fifo_misses_3 = history_3[-1]["fifo"]["misses"]
    
    history_4 = run_simulation(ops, cache_size=4, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    fifo_misses_4 = history_4[-1]["fifo"]["misses"]
    
    assert fifo_misses_4 > fifo_misses_3
    assert fifo_misses_3 == 9
    assert fifo_misses_4 == 10

def test_write_through_vs_write_back():
    trace = "W 1 A\nW 1 B\nW 1 C\nW 1 D\nR 2\nR 3\nW 2 E\nR 2\nR 2"
    ops = parse_trace(trace)
    
    wt_history = run_simulation(ops, cache_size=2, mode="Write-Through", hit_t=10, read_t=100, write_t=100, dirty_pct=0.5)
    wt_amat = wt_history[-1]["lru"]["amat"]
    
    wb_history = run_simulation(ops, cache_size=2, mode="Write-Back", hit_t=10, read_t=100, write_t=100, dirty_pct=0.5)
    wb_amat = wb_history[-1]["lru"]["amat"]
    
    assert wt_amat != wb_amat
