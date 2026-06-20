# Cache Simulator

A visual, step-by-step hardware cache simulator built with Streamlit. This application mathematically models cache behavior at the hardware level, fully simulating **Tag, Index, and Offset bit manipulation**, set-associativity, and block-aligned memory access.

It natively compares **Least Recently Used (LRU)** vs **First-In-First-Out (FIFO)** replacement policies side-by-side, rendering a real-time Cache Occupancy Heatmap to visually demonstrate cache pressure, thrashing, and Belady's Anomaly.

![Heatmap Demonstration](https://raw.githubusercontent.com/ayanava-99/cache-simulator/master/media/demo.png) *(Note: Add a screenshot here)*

## Core Features

- **True Hardware Modeling:** Configure Address Size (up to 64-bit), Cache Size, Block Size, and N-Way Associativity. The engine dynamically calculates and isolates `Tag`, `Index`, and `Offset` bits via bitwise operators for mathematically accurate block fetching.
- **Occupancy Heatmap UI:** A visual "bird's-eye" view of all cache sets. Instantly spot Set Conflicts and Thrashing without drowning in dataframes.
- **Dynamic Policy Showdown:** Watch LRU and FIFO react to the same memory trace side-by-side.
- **Write-Through vs Write-Back:** Tweak simulation timing (`T_hit`, `T_read`, `T_wb`) and observe how Write-Back delays Database (Memory) writes until a dirty eviction occurs.
- **Dynamic EMAT Calculation:** Calculates Effective Memory Access Time based on live hit/miss and dirty-eviction rates.

## Built-In Demonstration Traces

The simulator comes with 5 curated traces designed to mathematically trigger specific architecture phenomena:
1. **Spatial Locality:** Proves how a 4-byte block size turns 3 subsequent misses into 3 free hits by fetching neighboring bytes.
2. **Cache Thrashing (Conflict Misses):** Two addresses mapping to the exact same index kick each other out repeatedly—until you slide Associativity from 1 to 2!
3. **Belady's Anomaly:** An exact mathematical sequence that proves giving a FIFO cache *more memory* can make it perform *worse*.
4. **Write-Back Demo:** Shows how a Write-Back cache absorbs 3 immediate writes instantly, isolating main memory until a conflict forces a dirty eviction.
5. **Fast Divergence:** A standard trace highlighting how quickly LRU and FIFO naturally diverge.

## Installation & Usage

1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```bash
   streamlit run main.py
   ```

## Creating Custom Traces
You can upload your own `.txt` traces. The parser accepts hexadecimal memory addresses.

**Format:**
* Read: `R <hex_address>` (e.g., `R 0x1A2B`)
* Write: `W <hex_address> <optional_value>` (e.g., `W 0x1A2B DATA`)

Lines starting with `#` are ignored as comments.

## Project Structure

```text
├── main.py            # Streamlit UI, Heatmap rendering, and user input validation
├── engine.py          # Core hardware cache wrapper, bitwise math, and EMAT logic
├── parser.py          # Parses hexadecimal traces into int/string structures
├── database.py        # Simulated slow backing-store memory
├── lru.py             # LRU Set Associative logic
├── fifo.py            # FIFO Set Associative logic
├── test_engine.py     # Pytest suite asserting EMAT math, Write-Back delays, and Belady
├── requirements.txt   # Dependencies
├── .github/
│   └── workflows/     # CI/CD Pipeline (runs pytest on push)
└── traces/            # Built-in demonstration trace files
```
