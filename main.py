import streamlit as st
import pandas as pd
from parser import parse_trace
from engine import run_simulation
import math

st.set_page_config(page_title="Hardware Cache Simulator", layout="wide")
st.title("Hardware Cache Simulator")

st.sidebar.subheader("Hardware Configuration")
address_bits = st.sidebar.selectbox("Address Size (bits)", [16, 32, 64], index=0)
cache_size = st.sidebar.number_input("Cache Size (Bytes)", min_value=1, value=64, step=1)
block_size = st.sidebar.number_input("Block Size (Bytes)", min_value=1, value=4, step=1)

max_ways = cache_size // block_size
if max_ways < 1:
    st.sidebar.error("Cache Size must be >= Block Size")
    st.stop()

ways = st.sidebar.selectbox("Associativity (Ways)", [w for w in [1, 2, 4, 8, 16] if w <= max_ways], index=0)
mode = st.sidebar.selectbox("Write Mode", ["Write-Through", "Write-Back"])

st.sidebar.divider()
st.sidebar.subheader("Timing")
hit_t = st.sidebar.number_input("Cache time (T_hit) ms", min_value=1, value=10, step=1)
read_t = st.sidebar.number_input("DB read (T_read) ms", min_value=1, value=100, step=10)
write_t = st.sidebar.number_input("DB write (T_wb) ms", min_value=1, value=100, step=10)

dirty_pct = 0.0
if mode == "Write-Back":
    dirty_pct = st.sidebar.slider("% Dirty Evictions (for EMAT)", 0, 100, 50) / 100.0

st.sidebar.divider()
st.sidebar.subheader("Trace File")
src = st.sidebar.radio("Source", ["Belady's Anomaly", "Normal", "Fast Divergence", "Write-Back Demo", "Upload Custom Trace"])

raw_text = ""
if src == "Belady's Anomaly":
    with open("traces/beladys_anomaly.txt", "r") as f:
        raw_text = f.read()
elif src == "Normal":
    with open("traces/normal.txt", "r") as f:
        raw_text = f.read()
elif src == "Fast Divergence":
    with open("traces/divergence.txt", "r") as f:
        raw_text = f.read()
elif src == "Write-Back Demo":
    with open("traces/write_back_demo.txt", "r") as f:
        raw_text = f.read()
else:
    f_upload = st.sidebar.file_uploader("Upload .txt Trace", type=["txt"])
    if f_upload:
        raw_text = f_upload.getvalue().decode("utf-8")

if raw_text:
    with st.sidebar.expander("File Contents", expanded=True):
        st.code(raw_text, language=None)

if not raw_text:
    st.info("Please select or upload a trace file in the sidebar to begin.")
    st.stop()

sim_key = f"{address_bits}_{cache_size}_{block_size}_{ways}_{mode}_{hit_t}_{read_t}_{write_t}_{dirty_pct}_{raw_text}"
if "sim_key" not in st.session_state or st.session_state.sim_key != sim_key:
    try:
        ops = parse_trace(raw_text)
        st.session_state.history = run_simulation(
            ops, address_bits, cache_size, block_size, ways, mode, hit_t, read_t, write_t, dirty_pct
        )
        st.session_state.sim_key = sim_key
        st.session_state.idx = 0
    except Exception as e:
        st.error(f"Error parsing trace: {e}")
        st.stop()

history = st.session_state.history
if not history:
    st.warning("Trace file contained no valid operations.")
    st.stop()

st.subheader("Steps")
idx = st.slider("Step", 0, len(history), st.session_state.idx, label_visibility="collapsed")
st.session_state.idx = idx

btn_prev, btn_next, _ = st.columns([1, 1, 8])
if btn_prev.button("Prev Step") and st.session_state.idx > 0:
    st.session_state.idx -= 1
    st.rerun()
if btn_next.button("Next Step") and st.session_state.idx < len(history):
    st.session_state.idx += 1
    st.rerun()

st.divider()

if idx == 0:
    st.info("Simulation initialized. Press 'Next Step' or use the slider to begin.")
    st.stop()

now = history[idx - 1]
breakdown = now["breakdown"]

# Display operation breakdown banner
st.markdown(f"### Current Operation: `{now['raw']}`")
if breakdown:
    # Binary breakdown visuals
    # We recalculate the bits logic just for the UI rendering based on the breakdown dict.
    num_sets = cache_size // (block_size * ways)
    offset_bits = int(math.log2(block_size))
    index_bits = int(math.log2(num_sets))
    tag_bits = address_bits - index_bits - offset_bits
    
    st.info(f"**Tag ({tag_bits} bits):** `{breakdown['tag']}` | **Index ({index_bits} bits):** `{breakdown['index']}` | **Offset ({offset_bits} bits):** `{breakdown['offset']}`")

lru_emat = now['lru'].get('amat', 0)
fifo_emat = now['fifo'].get('amat', 0)

if lru_emat == fifo_emat:
    if lru_emat == 0:
        st.info("**Preferred Policy:** Both caches are warming up (EMAT is N/A).")
    else:
        st.info(f"**Preferred Policy:** It's a Tie! Both caches have an EMAT of {lru_emat:.1f} ms.")
elif lru_emat < fifo_emat:
    diff = fifo_emat - lru_emat
    st.success(f"**Preferred Policy: LRU Cache!** It is {diff:.1f} ms faster per access on average.")
else:
    diff = lru_emat - fifo_emat
    st.success(f"**Preferred Policy: FIFO Cache!** It is {diff:.1f} ms faster per access on average.")

def render_set_heatmap(sets_state, active_idx):
    for i, ways_arr in enumerate(sets_state):
        # active_idx can be None if the first step was a generic message without address breakdown, though here it's always set.
        is_active = (active_idx is not None and i == active_idx)
        with st.container(border=is_active):
            cols = st.columns([1] + [1] * len(ways_arr))
            cols[0].markdown(f"**Set {i}**")
            for j, way in enumerate(ways_arr):
                if way is None:
                    cols[j + 1].markdown(":gray[–]")
                elif way["dirty"]:
                    cols[j + 1].markdown(f":orange[●] `{way['tag']}`")
                else:
                    cols[j + 1].markdown(f":green[●] `{way['tag']}`")

def get_detail_df(sets_state, active_idx):
    if active_idx is None or active_idx >= len(sets_state):
        return pd.DataFrame(columns=["Way", "Tag", "Data", "Dirty"])
        
    active_ways = sets_state[active_idx]
    rows = []
    for j, way in enumerate(active_ways):
        if way is None:
            rows.append({"Way": j, "Tag": "-", "Data": "-", "Dirty": "-"})
        else:
            rows.append({"Way": j, "Tag": way["tag"], "Data": way["data"], "Dirty": "Yes" if way["dirty"] else "No"})
    return pd.DataFrame(rows)

c_left, c_right = st.columns(2)
active_idx = breakdown["index"] if breakdown else None

with c_left:
    st.subheader("LRU Cache")
    if "HIT" in now['lru']['msg']:
        st.success(now['lru']['msg'])
    elif "MISS" in now['lru']['msg']:
        st.error(now['lru']['msg'])
    else:
        st.info(now['lru']['msg'])
        
    st.markdown("##### Cache Occupancy Heatmap")
    render_set_heatmap(now['lru']['state'], active_idx)
    
    st.markdown(f"##### Set {active_idx} Detail (LRU)")
    st.dataframe(get_detail_df(now['lru']['state'], active_idx), use_container_width=True)
    
    st.markdown("##### Database (Memory)")
    if now['lru'].get('db_msg'):
        st.warning(now['lru']['db_msg'])
    
    db_df = pd.DataFrame([{"Block Addr": k, "Data": v} for k, v in now['lru']['db_state'].items()])
    st.dataframe(db_df if not db_df.empty else pd.DataFrame(columns=["Block Addr", "Data"]), use_container_width=True, height=200)
    
    st.markdown("#### Stats")
    st.write(f"**Hits:** {now['lru']['hits']} | **Misses:** {now['lru']['misses']} | **Evictions:** {now['lru']['evictions']}")
    tot = now['lru']['hits'] + now['lru']['misses']
    st.write(f"**Hit Rate:** {now['lru']['hits']/tot*100:.1f}%" if tot > 0 else "**Hit Rate:** -")
    st.markdown(now['lru'].get('amat_str', f"**EMAT:** {now['lru'].get('amat', 0):.1f} ms"))

with c_right:
    st.subheader("FIFO Cache")
    if "HIT" in now['fifo']['msg']:
        st.success(now['fifo']['msg'])
    elif "MISS" in now['fifo']['msg']:
        st.error(now['fifo']['msg'])
    else:
        st.info(now['fifo']['msg'])
        
    st.markdown("##### Cache Occupancy Heatmap")
    render_set_heatmap(now['fifo']['state'], active_idx)
    
    st.markdown(f"##### Set {active_idx} Detail (FIFO)")
    st.dataframe(get_detail_df(now['fifo']['state'], active_idx), use_container_width=True)
    
    st.markdown("##### Database (Memory)")
    if now['fifo'].get('db_msg'):
        st.warning(now['fifo']['db_msg'])
        
    db_df_fifo = pd.DataFrame([{"Block Addr": k, "Data": v} for k, v in now['fifo']['db_state'].items()])
    st.dataframe(db_df_fifo if not db_df_fifo.empty else pd.DataFrame(columns=["Block Addr", "Data"]), use_container_width=True, height=200)
    
    st.markdown("#### Stats")
    st.write(f"**Hits:** {now['fifo']['hits']} | **Misses:** {now['fifo']['misses']} | **Evictions:** {now['fifo']['evictions']}")
    tot = now['fifo']['hits'] + now['fifo']['misses']
    st.write(f"**Hit Rate:** {now['fifo']['hits']/tot*100:.1f}%" if tot > 0 else "**Hit Rate:** -")
    st.markdown(now['fifo'].get('amat_str', f"**EMAT:** {now['fifo'].get('amat', 0):.1f} ms"))
