import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # allow `from src...` under `streamlit run`

import pandas as pd
import streamlit as st

from src.pipeline import Pipeline
from src.reranker import THRESHOLD
from src.rewriter import EmptyQueryError

st.set_page_config(page_title="Two-Stage RAG", layout="wide")


@st.cache_resource(show_spinner="Loading models and index...")
def get_pipeline() -> Pipeline:
    return Pipeline()


st.session_state.setdefault("history", [])
st.session_state.setdefault("result", None)

st.title("Cloud Infrastructure Assistant")
st.caption("Two-stage RAG: rewrite -> bi-encoder top 20 -> cross-encoder re-rank -> confidence gate -> internal docs or web fallback")

multi_turn = st.toggle("Multi-turn conversational follow-ups", value=False)
if multi_turn and st.session_state.history:
    st.caption("Context: " + " | ".join(st.session_state.history[-3:]))

with st.form("query_form", clear_on_submit=False):
    query = st.text_input("Ask a question", placeholder="How do I provision an isolated VPC in our staging environment?")
    c1, c2 = st.columns([1, 6])
    submitted = c1.form_submit_button("Search")
    if c2.form_submit_button("Clear conversation"):
        st.session_state.history = []
        st.session_state.result = None

if submitted:
    try:
        with st.spinner("Running pipeline..."):
            history = st.session_state.history if multi_turn else None
            st.session_state.result = get_pipeline().run(query, history=history)
        st.session_state.history.append(query.strip())
    except EmptyQueryError:
        st.error("Please enter a question.")
    except Exception as e:
        st.error(f"Pipeline error: {e}")

result = st.session_state.result

# ---------- Sidebar telemetry ----------
with st.sidebar:
    st.header("Pipeline telemetry")
    if result is None:
        st.info("Run a query to see telemetry.")
    else:
        r = result.response
        st.subheader("Transformed query")
        st.code(r.transformed_query, language=None)

        st.subheader("Route")
        if r.route_taken == "INTERNAL_RAG":
            st.markdown(":green-background[🟢 INTERNAL_RAG (High Confidence)]")
        else:
            st.markdown(":orange-background[🟠 WEB_FALLBACK (Low Confidence Triggered)]")

        st.subheader("Confidence")
        st.metric("Top cross-encoder score", f"{r.confidence_score:.3f}", f"threshold {THRESHOLD}", delta_color="off")
        st.progress(min(max(r.confidence_score, 0.0), 1.0))
        st.caption(f"{'≥' if r.confidence_score >= THRESHOLD else '<'} {THRESHOLD} cutoff")

if result is None:
    st.stop()

# ---------- Answer with citation popovers ----------
st.subheader("Answer")
st.markdown(result.response.answer)

if result.context:
    st.caption("Sources (click to inspect)")
    cols = st.columns(len(result.context))
    for i, (col, chunk) in enumerate(zip(cols, result.context), 1):
        with col.popover(f"[{i}] {'web' if chunk.source == 'web' else 'doc'}"):
            if chunk.source == "web":
                st.markdown(f"[{chunk.chunk_id}]({chunk.chunk_id})")
            else:
                st.markdown(f"**{chunk.chunk_id}**")
            st.text(chunk.content)  # plain text: never render untrusted content as markdown

# ---------- Two-stage retrieval visualizer ----------
with st.expander(f"Stage 1: Bi-encoder top {len(result.stage1)} candidates", expanded=False):
    st.dataframe(
        pd.DataFrame(
            [{"rank": i, "chunk_id": c.chunk_id, "cosine similarity": round(c.score, 4)} for i, c in enumerate(result.stage1, 1)]
        ),
        hide_index=True,
    )

with st.expander("Stage 2: Cross-encoder re-ranked top 5", expanded=True):
    rows = []
    for i, c in enumerate(result.reranked[:5], 1):
        shift = result.shifts.get(c.chunk_id, 0)
        arrow = f"↑{shift}" if shift > 0 else (f"↓{-shift}" if shift < 0 else "–")
        rows.append({"rank": i, "stage 1 rank": i + shift, "shift": arrow, "chunk_id": c.chunk_id, "confidence (sigmoid)": round(c.score, 4)})
    st.dataframe(pd.DataFrame(rows), hide_index=True)
