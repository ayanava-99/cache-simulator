import streamlit as st
import pandas as pd
from parser import parse_trace
from engine import run_simulation

st.set_page_config(page_title="Cache Simulator", layout="wide")
st.title("Cache Simulator")

st.sidebar.subheader("Cache Configuration")
cap = st.sidebar.slider("Cache Capacity", min_value=1, max_value=10, value=3)
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

sim_key = f"{cap}_{mode}_{hit_t}_{read_t}_{write_t}_{dirty_pct}_{raw_text}"
if "sim_key" not in st.session_state or st.session_state.sim_key != sim_key:
    try:
        ops = parse_trace(raw_text)
        st.session_state.history = run_simulation(ops, cap, mode, hit_t, read_t, write_t, dirty_pct)
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
st.markdown(f"### Current Operation: `{now['raw']}`")

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

lru_last = history[idx-2]['lru']['state'] if idx > 1 else []
fifo_last = history[idx-2]['fifo']['state'] if idx > 1 else []

lru_db_last = history[idx-2]['lru']['db_state'] if idx > 1 else {}
fifo_db_last = history[idx-2]['fifo']['db_state'] if idx > 1 else {}

def color_df(state, prev_state):
    df = pd.DataFrame(state) if state else pd.DataFrame(columns=["Position", "Key", "Value", "Status"])
    prev_df = pd.DataFrame(prev_state) if prev_state else pd.DataFrame(columns=["Position", "Key", "Value", "Status"])
    
    def apply_highlight(row):
        i = row.name
        if i >= len(prev_df):
            return ['background-color: rgba(40, 167, 69, 0.2)'] * len(row)
        elif df.iloc[i].to_dict() != prev_df.iloc[i].to_dict():
            return ['background-color: rgba(255, 193, 7, 0.2)'] * len(row)
        return [''] * len(row)
        
    if not df.empty:
        return df.style.apply(apply_highlight, axis=1)
    return df

def format_db_df(db_dict):
    df = pd.DataFrame([{"Key": k, "Value": v} for k, v in db_dict.items()])
    if not df.empty:
        df['SortKey'] = pd.to_numeric(df['Key'], errors='coerce')
        df = df.sort_values(by=['SortKey', 'Key']).drop('SortKey', axis=1).reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=["Key", "Value"])
    return df

def color_db_df(state_dict, prev_state_dict):
    df = format_db_df(state_dict)
    if df.empty: return df
    
    prev_dict = prev_state_dict if prev_state_dict else {}
    
    def apply_highlight(row):
        k = row['Key']
        v = row['Value']
        if k not in prev_dict:
            return ['background-color: rgba(40, 167, 69, 0.2)'] * len(row)
        elif prev_dict[k] != v:
            return ['background-color: rgba(255, 193, 7, 0.2)'] * len(row)
        return [''] * len(row)
        
    return df.style.apply(apply_highlight, axis=1)

c_left, c_right = st.columns(2)

with c_left:
    st.subheader("LRU Cache")
    
    if "HIT" in now['lru']['msg']:
        st.success(now['lru']['msg'])
    elif "MISS" in now['lru']['msg']:
        st.error(now['lru']['msg'])
    else:
        st.info(now['lru']['msg'])
        
    st.dataframe(color_df(now['lru']['state'], lru_last), use_container_width=True)
    
    st.markdown("#### Database")
    if now['lru'].get('db_msg'):
        st.warning(now['lru']['db_msg'])
    st.dataframe(color_db_df(now['lru']['db_state'], lru_db_last), use_container_width=True, height=200)
    
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
        
    st.dataframe(color_df(now['fifo']['state'], fifo_last), use_container_width=True)
    
    st.markdown("#### Database")
    if now['fifo'].get('db_msg'):
        st.warning(now['fifo']['db_msg'])
    st.dataframe(color_db_df(now['fifo']['db_state'], fifo_db_last), use_container_width=True, height=200)
    
    st.markdown("#### Stats")
    st.write(f"**Hits:** {now['fifo']['hits']} | **Misses:** {now['fifo']['misses']} | **Evictions:** {now['fifo']['evictions']}")
    tot = now['fifo']['hits'] + now['fifo']['misses']
    st.write(f"**Hit Rate:** {now['fifo']['hits']/tot*100:.1f}%" if tot > 0 else "**Hit Rate:** -")
    st.markdown(now['fifo'].get('amat_str', f"**EMAT:** {now['fifo'].get('amat', 0):.1f} ms"))
