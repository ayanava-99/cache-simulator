# Write-Through / Write-Back Cache Simulator

Interactive cache simulator built with Python and Streamlit.
Demonstrates LRU and FIFO eviction policies with write-through and write-back modes.

## Features

- **Eviction Policies**: LRU (Least Recently Used) and FIFO (First In First Out)
- **Write Modes**: Write-Through and Write-Back
- **Time Calculation**: User-configurable cache and DB access times
- **Visual Cache Blocks**: See items move in real time

## Architecture

```
┌─────────┐      ┌──────────────┐      ┌──────────┐
│  Client  │ ──→ │    Cache     │ ──→  │ Database │
│ (Browser)│ ←── │ (LRU / FIFO) │ ←──  │ (dict)   │
└─────────┘      └──────────────┘      └──────────┘

Write-Through: PUT writes to cache AND database immediately
Write-Back:    PUT writes to cache only, database updated on eviction
```

## How to Run

```bash
pip install streamlit
python -m streamlit run app.py
```

## Project Structure

```
LRU/
├── app.py           # Streamlit UI
├── cache_lru.py     # LRU eviction policy (OrderedDict + move_to_end)
├── cache_fifo.py    # FIFO eviction policy (OrderedDict, no reordering)
├── slow_database.py # Simulated database (dict)
├── requirements.txt
└── README.md
```

## Key Difference: LRU vs FIFO

| Feature       | LRU                        | FIFO                        |
|---------------|----------------------------|-----------------------------|
| On GET hit    | Moves item to end (MRU)    | No movement                 |
| Evicts        | Least recently used        | First inserted              |
| Key method    | `move_to_end()` on access  | No reordering               |

## Key Difference: Write-Through vs Write-Back

| Feature        | Write-Through              | Write-Back                  |
|----------------|----------------------------|-----------------------------|
| On PUT         | Write to cache + DB        | Write to cache only         |
| DB consistency | Always in sync             | May be stale until eviction |
| PUT speed      | Slower (cache + DB time)   | Faster (cache time only)    |
| On eviction    | Nothing extra              | Write dirty entry to DB     |
