import pytest
from engine import run_simulation
from parser import parse_trace

def test_beladys_anomaly():
    """Verify that FIFO cache exhibits Belady's Anomaly (more capacity = more misses)."""
    # Standard trace demonstrating Belady's Anomaly
    trace = "R 0x1000\nR 0x2000\nR 0x3000\nR 0x4000\nR 0x1000\nR 0x2000\nR 0x5000\nR 0x1000\nR 0x2000\nR 0x3000\nR 0x4000\nR 0x5000"
    ops = parse_trace(trace)
    
    # Run with ways=3 (Directly replacing capacity parameter)
    history_3 = run_simulation(ops, address_bits=16, cache_size=12, block_size=4, ways=3, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    fifo_misses_3 = history_3[-1]["fifo"]["misses"]
    
    # Run with ways=4
    history_4 = run_simulation(ops, address_bits=16, cache_size=16, block_size=4, ways=4, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    fifo_misses_4 = history_4[-1]["fifo"]["misses"]
    
    # The anomaly: capacity 4 has STRICTLY MORE misses than capacity 3
    assert fifo_misses_4 > fifo_misses_3, f"Belady's Anomaly failed: Misses(C=3)={fifo_misses_3}, Misses(C=4)={fifo_misses_4}"
    assert fifo_misses_3 == 9
    assert fifo_misses_4 == 10

def test_emat_calculation():
    """Verify EMAT matches manual calculation for a simple trace."""
    # 5 reads, capacity 10 -> 0 capacity evictions.
    # Read 1: MISS (hit_t + read_t + hit_t) = 10 + 100 + 10 = 120 ms
    # Read 1: HIT (hit_t) = 10 ms
    # Read 2: MISS (120 ms)
    # Read 2: HIT (10 ms)
    # Total hits=2, misses=2 -> Miss Rate = 0.5
    # Write-Through EMAT: hit_t + (MR * read_t) = 10 + (0.5 * 100) = 60.0 ms
    
    trace = "R 0x1000\nR 0x1000\nR 0x2000\nR 0x2000"
    ops = parse_trace(trace)
    # Using small capacity to avoid math issues with hardware set splits
    history = run_simulation(ops, address_bits=16, cache_size=16, block_size=4, ways=4, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    
    final_lru_state = history[-1]["lru"]
    assert final_lru_state["hits"] == 2
    assert final_lru_state["misses"] == 2
    assert final_lru_state["amat"] == 60.0

def test_write_back_delayed_db_writes():
    """Verify that Write-Back mode delays DB writes until eviction."""
    # Write 1 (dirty in cache, DB unchanged)
    # Write 2 (dirty in cache, DB unchanged)
    # Read 3 (Miss, causes eviction of 1. DB gets updated with 1)
    
    trace = "W 0x1000 NEW_A\nW 0x2000 NEW_B\nR 0x3000"
    ops = parse_trace(trace)
    
    history = run_simulation(ops, address_bits=16, cache_size=8, block_size=4, ways=2, mode="Write-Back", hit_t=10, read_t=100, write_t=100)
    
    # Step 1: W 0x1000 NEW_A
    state_step_1 = history[0]["lru"]
    assert state_step_1["db_state"].get("0x1000") != "NEW_A", "DB should not be updated immediately in Write-Back"
    
    # Step 3: R 0x3000 (Evicts 0x1000 since capacity is 2 per set and they all map to set 0)
    state_step_3 = history[2]["lru"]
    assert state_step_3["db_state"].get("0x1000") == "NEW_A", "DB should be updated after dirty eviction"
    assert "DB UPDATED" in state_step_3["db_msg"], "Engine should log DB update on dirty eviction"
