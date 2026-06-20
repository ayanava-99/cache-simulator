# Cache Simulator

An interactive, trace-driven cache simulator built with Python and Streamlit. This tool is designed to help students and developers visualize how different caching algorithms behave step-by-step under exactly the same workload.

It runs a side-by-side comparison of **LRU (Least Recently Used)** and **FIFO (First In First Out)** replacement policies. 

## Features

- **Trace-Driven**: Replay operations step-by-step using plain text trace files (e.g. `R 1`, `W 2 APPLE`).
- **Policy Comparison**: Watch LRU and FIFO caches process the exact same operations in lockstep.
- **Write Modes**: Toggle between **Write-Through** and **Write-Back** caching.
- **Delayed Writes**: Watch the database visually fall out of sync from the cache when using Write-Back, updating only upon dirty evictions!
- **Dynamic Benchmarking**: Real-time calculation of **EMAT (Effective Memory Access Time)**, explicitly declaring which policy is faster for the current workload.
- **Belady's Anomaly Demo**: Includes built-in trace files designed specifically to trigger Belady's Anomaly (where increasing cache size *increases* miss rate).

## How to Run

1. Ensure you have Streamlit installed:
```bash
pip install streamlit pandas
```

2. Launch the application:
```bash
python -m streamlit run main.py
```

## Project Structure

```text
LRU/
├── main.py        # Streamlit User Interface
├── engine.py      # Core simulation engine that computes timelines
├── parser.py      # Parses text trace files into commands
├── lru.py         # LRU cache implementation
├── fifo.py        # FIFO cache implementation
├── database.py    # Mock database backend
└── traces/        # Directory containing built-in trace demo files
```

## Built-In Trace Demos

- **Normal**: A standard mix of reads and writes.
- **Belady's Anomaly**: Designed to show FIFO performing worse when given more capacity.
- **Fast Divergence**: Forces LRU and FIFO to make different eviction choices early on.
- **Write-Back Demo**: Explicitly forces dirty evictions to demonstrate delayed database writes.
