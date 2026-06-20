import pytest
from engine import run_simulation
from parser import parse_trace

def test_beladys_anomaly():
    """Verify that FIFO cache exhibits Belady's Anomaly (more capacity = more misses)."""
    trace = "R 0x10\nR 0x20\nR 0x30\nR 0x40\nR 0x10\nR 0x20\nR 0x50\nR 0x10\nR 0x20\nR 0x30\nR 0x40\nR 0x50"
    ops = parse_trace(trace)
    
    # Run with ways=3 (cache=12)
    history_3 = run_simulation(ops, address_bits=8, cache_size=12, block_size=4, ways=3, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    fifo_misses_3 = history_3[-1]["fifo"]["misses"]
    
    # Run with ways=4 (cache=16)
    history_4 = run_simulation(ops, address_bits=8, cache_size=16, block_size=4, ways=4, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    fifo_misses_4 = history_4[-1]["fifo"]["misses"]
    
    # The anomaly: capacity 4 has STRICTLY MORE misses than capacity 3
    assert fifo_misses_4 > fifo_misses_3, f"Belady's Anomaly failed: Misses(C=3)={fifo_misses_3}, Misses(C=4)={fifo_misses_4}"
    assert fifo_misses_3 == 9
    assert fifo_misses_4 == 10

def test_emat_calculation():
    """Verify EMAT matches manual calculation for a simple trace."""
    # Read 1: MISS (hit_t + read_t + hit_t) = 120 ms
    # Read 1: HIT (10 ms)
    # Read 2: MISS (120 ms)
    # Read 2: HIT (10 ms)
    # Total hits=2, misses=2 -> Miss Rate = 0.5
    # Write-Through EMAT: hit_t + (MR * (read_t + hit_t)) = 10 + (0.5 * 110) = 65.0 ms
    
    trace = "R 0x10\nR 0x10\nR 0x20\nR 0x20"
    ops = parse_trace(trace)
    history = run_simulation(ops, address_bits=8, cache_size=16, block_size=4, ways=4, mode="Write-Through", hit_t=10, read_t=100, write_t=100)
    
    final_lru_state = history[-1]["lru"]
    assert final_lru_state["hits"] == 2
    assert final_lru_state["misses"] == 2
    assert final_lru_state["amat"] == 65.0

def test_write_back_delayed_db_writes():
    """Verify that Write-Back mode delays DB writes until eviction."""
    trace = "W 0x10 NEW_A\nW 0x20 NEW_B\nR 0x30"
    ops = parse_trace(trace)
    
    history = run_simulation(ops, address_bits=8, cache_size=8, block_size=4, ways=2, mode="Write-Back", hit_t=10, read_t=100, write_t=100)
    
    # Step 1: W 0x10 NEW_A — DB should NOT be updated yet
    state_step_1 = history[0]["lru"]
    assert state_step_1["db_state"].get("0x10") != "NEW_A", "DB should not be updated immediately in Write-Back"
    
    # Step 3: R 0x30 (Evicts 0x10 since capacity is 2 and all map to set 0)
    state_step_3 = history[2]["lru"]
    assert state_step_3["db_state"].get("0x10") == "NEW_A", "DB should be updated after dirty eviction"
    assert "DB UPDATED" in state_step_3["db_msg"], "Engine should log DB update on dirty eviction"
