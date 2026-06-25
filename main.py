import streamlit as st
import pandas as pd
from parser import parse_trace
from engine import run_simulation

st.set_page_config(page_title="Cache Simulator", layout="wide")
st.title("Cache Simulator")

st.sidebar.subheader("Configuration")
cache_size=st.sidebar.number_input("Cache Capacity (items)", min_value=1, max_value=32, value=4)
mode= st.sidebar.selectbox("Write Mode", ["Write-Through", "Write-Back"])

st.sidebar.divider()
st.sidebar.subheader("Timing")
hit_t= st.sidebar.number_input("Cache time (T_hit) ms", min_value=1, value=10, step=1)
read_t=st.sidebar.number_input("DB read (T_read) ms", min_value=1, value=100, step=10)
write_t =st.sidebar.number_input("DB write (T_wb) ms", min_value=1, value=100, step=10)

dirty_pct=0.0
if mode=="Write-Back":
    dirty_pct= st.sidebar.slider("% Dirty Evictions (for EMAT)", 0, 100, 50) / 100.0

st.sidebar.divider()
st.sidebar.subheader("Trace File")
src= st.sidebar.radio("Source", ["LRU vs FIFO Demo", "Write-Back Demo", "Belady's Anomaly Demo", "Upload Custom Trace"])

raw_text= ""
if src=="Write-Back Demo":
    with open("traces/write_back_demo.txt", "r") as f:
        raw_text=f.read()
elif src=="LRU vs FIFO Demo":
    with open("traces/lru_vs_fifo_demo.txt", "r") as f:
        raw_text= f.read()
elif src=="Belady's Anomaly Demo":
    with open("traces/beladys_anomaly_demo.txt", "r") as f:
        raw_text= f.read()
else:
    f_upload= st.sidebar.file_uploader("Upload .txt Trace", type=["txt"])
    if f_upload:
        raw_text=f_upload.getvalue().decode("utf-8")

if raw_text:
    with st.sidebar.expander("File Contents", expanded=True):
        st.code(raw_text, language=None)

if not raw_text:
    st.info("Please select or upload a trace file in the sidebar to begin.")
    st.stop()

st.sidebar.divider()
st.sidebar.markdown(
    '[![View on GitHub](https://img.shields.io/badge/View_on_GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ayanava-99/cache-simulator)'
)

sim_key= f"{cache_size}_{mode}_{hit_t}_{read_t}_{write_t}_{dirty_pct}_{raw_text}"
if "sim_key" not in st.session_state or st.session_state.sim_key!=sim_key:
    try:
        ops= parse_trace(raw_text)
        st.session_state.history=run_simulation(
            ops, cache_size, mode, hit_t, read_t, write_t, dirty_pct
        )
        st.session_state.sim_key=sim_key
        st.session_state.idx= 0
    except Exception as e:
        st.error(f"Error parsing trace: {e}")
        st.stop()

history=st.session_state.history
if not history:
    st.warning("Trace file contained no valid operations.")
    st.stop()

st.subheader("Steps")
idx=st.slider("Step", 0, len(history) - 1, st.session_state.idx, label_visibility="collapsed")
st.session_state.idx= idx

btn_prev, btn_next, _= st.columns([1, 1, 8])
if btn_prev.button("Prev Step") and st.session_state.idx>0:
    st.session_state.idx-=1
    st.rerun()
if btn_next.button("Next Step") and st.session_state.idx < len(history) - 1:
    st.session_state.idx+= 1
    st.rerun()

st.divider()

now= history[idx]

st.markdown(f"### Current Operation: `{now['raw']}`")

lru_emat= now['lru'].get('amat', 0)
fifo_emat=now['fifo'].get('amat', 0)

if lru_emat==fifo_emat:
    if lru_emat== 0:
        st.info("**Preferred Policy:** Both caches are warming up (EMAT is N/A).")
    else:
        st.info(f"**Preferred Policy:** It's a Tie! Both caches have an EMAT of {lru_emat:.1f} ms.")
elif lru_emat < fifo_emat:
    diff=fifo_emat - lru_emat
    st.success(f"**Preferred Policy: LRU Cache!** It is {diff:.1f} ms faster per access on average.")
else:
    diff=lru_emat - fifo_emat
    st.success(f"**Preferred Policy: FIFO Cache!** It is {diff:.1f} ms faster per access on average.")

def render_cache_list(cache_state):
    rows= []
    for j, item in enumerate(cache_state):
        if item is None:
            rows.append({"Index": j, "Key": "-", "Data": "-", "Dirty": "-"})
        else:
            rows.append({"Index": j, "Key": item["key"], "Data": item["data"], "Dirty": "Yes" if item["dirty"] else "No"})
    return pd.DataFrame(rows)

c_left, c_right=st.columns(2)

with c_left:
    st.subheader("LRU Cache")
    if "HIT" in now['lru']['msg']:
        st.success(now['lru']['msg'])
    elif "MISS" in now['lru']['msg']:
        st.error(now['lru']['msg'])
    else:
        st.info(now['lru']['msg'])
        
    st.markdown("##### Cache State")
    st.dataframe(render_cache_list(now['lru']['state']), use_container_width=True)
    
    st.markdown("##### Database (Memory)")
    if now['lru'].get('db_msg'):
        st.warning(now['lru']['db_msg'])
    
    db_df= pd.DataFrame([{"Key": k, "Data": v} for k, v in now['lru']['db_state'].items()])
    if not db_df.empty:
        updated_key_lru= now['lru'].get('db_updated_key')
        def highlight_lru(row):
            if row['Key']== updated_key_lru:
                return ['background-color: rgba(46, 125, 50, 0.5)'] * len(row)
            return [''] * len(row)
        st.dataframe(db_df.style.apply(highlight_lru, axis=1), use_container_width=True, height=200)
    else:
        st.dataframe(pd.DataFrame(columns=["Key", "Data"]), use_container_width=True, height=200)
    
    st.markdown("#### Stats")
    st.write(f"**Hits:** {now['lru']['hits']} | **Misses:** {now['lru']['misses']} | **Evictions:** {now['lru']['evictions']}")
    tot= now['lru']['hits'] + now['lru']['misses']
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
        
    st.markdown("##### Cache State")
    st.dataframe(render_cache_list(now['fifo']['state']), use_container_width=True)
    
    st.markdown("##### Database (Memory)")
    if now['fifo'].get('db_msg'):
        st.warning(now['fifo']['db_msg'])
        
    db_df_fifo= pd.DataFrame([{"Key": k, "Data": v} for k, v in now['fifo']['db_state'].items()])
    if not db_df_fifo.empty:
        updated_key_fifo= now['fifo'].get('db_updated_key')
        def highlight_fifo(row):
            if row['Key']==updated_key_fifo:
                return ['background-color: rgba(46, 125, 50, 0.5)'] * len(row)
            return [''] * len(row)
        st.dataframe(db_df_fifo.style.apply(highlight_fifo, axis=1), use_container_width=True, height=200)
    else:
        st.dataframe(pd.DataFrame(columns=["Key", "Data"]), use_container_width=True, height=200)
    
    st.markdown("#### Stats")
    st.write(f"**Hits:** {now['fifo']['hits']} | **Misses:** {now['fifo']['misses']} | **Evictions:** {now['fifo']['evictions']}")
    tot= now['fifo']['hits'] + now['fifo']['misses']
    st.write(f"**Hit Rate:** {now['fifo']['hits']/tot*100:.1f}%" if tot > 0 else "**Hit Rate:** -")
    st.markdown(now['fifo'].get('amat_str', f"**EMAT:** {now['fifo'].get('amat', 0):.1f} ms"))

st.divider()
st.subheader("EMAT Over Time")

chart_rows= []
for s in history[:idx + 1]:
    if s["step"]==0: continue
    chart_rows.append({
        "Step": s["step"],
        "LRU": s["lru"]["amat"],
        "FIFO": s["fifo"]["amat"],
    })

if chart_rows:
    chart_df=pd.DataFrame(chart_rows).set_index("Step")
    st.line_chart(chart_df, use_container_width=True, color=["#1E90FF", "#FF4B4B"])
