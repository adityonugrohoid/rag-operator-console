"""RAG Operator Console - RAG pipeline with full observability."""
import os
import glob as glob_module

import streamlit as st
import requests

st.set_page_config(page_title="RAG Operator Console", layout="wide")
st.title("RAG Operator Console")

API_URL = os.getenv("API_URL", "http://localhost:8080")

AVAILABLE_MODELS = [
    {"id": "llama3.2:3b", "size": "2.0GB", "tier": "Meta"},
    {"id": "qwen2.5:3b", "size": "1.9GB", "tier": "Alibaba"},
    {"id": "phi3.5:3.8b", "size": "2.2GB", "tier": "Microsoft"},
]

MODEL_OPTIONS = [m["id"] for m in AVAILABLE_MODELS]

# -------------------------------------------------------------------------
# Sidebar: Model selection + Parameters + Document Management + Status
# -------------------------------------------------------------------------
with st.sidebar:
    st.header("Model Selection")
    # Default to llama3.2:3b (index 0) for initial selection
    selected_model = st.selectbox("Active Model", MODEL_OPTIONS, index=0)
    model_info = next(m for m in AVAILABLE_MODELS if m["id"] == selected_model)
    st.caption(f"Size: {model_info['size']} | Tier: {model_info['tier']}")

    st.divider()
    st.header("Parameters")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 64, 2048, 512, 64)

    st.divider()
    st.header("Document Management")

    # Show indexed document count
    try:
        docs_resp = requests.get(f"{API_URL}/documents", timeout=5)
        if docs_resp.status_code == 200:
            docs_data = docs_resp.json()
            doc_count = docs_data.get("count", 0)
            st.metric("Indexed Documents", doc_count)
            if doc_count > 0:
                with st.expander("Document list"):
                    for doc_name in docs_data.get("documents", []):
                        st.text(doc_name)
        else:
            st.metric("Indexed Documents", "?")
    except requests.RequestException:
        st.metric("Indexed Documents", "?")

    # Upload document
    uploaded_file = st.file_uploader("Upload document", type=["txt", "pdf", "docx"])
    if uploaded_file and st.button("Ingest"):
        with st.spinner("Ingesting..."):
            try:
                resp = requests.post(
                    f"{API_URL}/documents/upload",
                    files={"file": (uploaded_file.name, uploaded_file.read(),
                                    uploaded_file.type)},
                    timeout=60,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    st.success(
                        f"Ingested: {result['chunks_created']} chunks"
                        + (" (PII detected)" if result.get("pii_detected") else "")
                    )
                    st.rerun()
                else:
                    st.error(f"Ingestion failed: {resp.text}")
            except requests.RequestException as e:
                st.error(f"Ingestion error: {e}")

    # Clear database
    if st.button("Clear Database"):
        try:
            resp = requests.delete(f"{API_URL}/documents", timeout=30)
            if resp.status_code == 200:
                st.success("Database cleared")
                st.rerun()
            else:
                st.error(f"Clear failed: {resp.text}")
        except requests.RequestException as e:
            st.error(f"Clear error: {e}")

    # Bulk ingest sample docs
    if st.button("Ingest Sample Docs"):
        doc_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "documents",
        )
        txt_files = sorted(glob_module.glob(os.path.join(doc_dir, "**", "*.txt"), recursive=True))
        if not txt_files:
            st.warning("No sample documents found")
        else:
            progress = st.progress(0)
            for idx, fp in enumerate(txt_files):
                fname = os.path.basename(fp)
                with open(fp, "rb") as f:
                    try:
                        requests.post(
                            f"{API_URL}/documents/upload",
                            files={"file": (fname, f, "text/plain")},
                            timeout=60,
                        )
                    except requests.RequestException:
                        pass
                progress.progress((idx + 1) / len(txt_files))
            st.success(f"Ingested {len(txt_files)} documents")
            st.rerun()

    st.divider()
    # Service status
    try:
        health = requests.get(f"{API_URL}/health", timeout=5).json()
        overall = health.get("status", "unknown")
        color = "green" if overall == "healthy" else "red"
        st.markdown(f"Services: :{color}[{overall}]")
    except requests.RequestException:
        st.markdown("Services: :red[unreachable]")


# -------------------------------------------------------------------------
# Main area: RAG Query (with 1-turn clarification context)
# -------------------------------------------------------------------------
if "prev_question" not in st.session_state:
    st.session_state.prev_question = None
    st.session_state.prev_answer = None

# Show previous turn context if available
if st.session_state.prev_question:
    with st.expander("Previous turn (used as clarification context)", expanded=False):
        st.markdown(f"**Q:** {st.session_state.prev_question}")
        st.markdown(f"**A:** {st.session_state.prev_answer[:300]}...")
    if st.button("Clear context", key="clear_ctx"):
        st.session_state.prev_question = None
        st.session_state.prev_answer = None
        st.rerun()

rag_query = st.text_area("Enter your question:", height=150, key="rag_prompt")

if st.button("Query RAG", type="primary", disabled=not rag_query, key="rag_btn"):
    # Build clarification context from previous turn
    clarification_context = None
    if st.session_state.prev_question and st.session_state.prev_answer:
        clarification_context = (
            f"Q: {st.session_state.prev_question}\n"
            f"A: {st.session_state.prev_answer}"
        )

    with st.spinner(f"Querying RAG pipeline with {selected_model}..."):
        try:
            payload = {
                "query": rag_query,
                "model": selected_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if clarification_context:
                payload["clarification_context"] = clarification_context

            resp = requests.post(
                f"{API_URL}/query",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()

            # Store current turn as context for next query
            st.session_state.prev_question = rag_query
            st.session_state.prev_answer = result.get("answer", "")

            # --- Response Area ---
            st.markdown("### Answer")
            st.write(result.get("answer", ""))

            sources = result.get("sources", [])
            if sources:
                st.markdown(
                    "**Sources:** "
                    + ", ".join(f"`{s}`" for s in sources)
                )

            # --- Pipeline Metrics Bar ---
            metrics = result.get("pipeline_metrics", {})
            st.markdown("---")
            st.markdown("### Pipeline Metrics")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Retrieval", f"{metrics.get('retrieval_ms', 0):.0f} ms")
            m2.metric("Assembly", f"{metrics.get('assembly_ms', 0):.0f} ms")
            m3.metric("LLM", f"{metrics.get('llm_ms', 0):.0f} ms")
            m4.metric("Total", f"{metrics.get('total_ms', 0):.0f} ms")

            t1, t2, t3 = st.columns(3)
            t1.metric("Model", result.get("model", ""))
            t2.metric("Tokens Generated", metrics.get("tokens_generated", 0))
            t3.metric(
                "Throughput",
                f"{metrics.get('tokens_per_sec', 0):.1f} tok/s",
            )

            # --- Prompt Assembly Panel ---
            assembly = result.get("prompt_assembly", {})
            with st.expander("Prompt Assembly Debug", expanded=False):
                budget = assembly.get("budget", 0)
                total_tok = assembly.get("total_tokens", 0)

                layers = [
                    (
                        "Layer 1: System Instructions",
                        assembly.get("system_tokens", 0),
                        "PINNED",
                    ),
                    (
                        "Layer 2: Retrieved Documents",
                        assembly.get("retrieved_docs_tokens", 0),
                        "PINNED",
                    ),
                    (
                        "Layer 3: Clarification Context",
                        assembly.get("clarification_tokens", 0),
                        "PINNED" if assembly.get("clarification_included") else "DROPPED",
                    ),
                    (
                        "Layer 4: User Question",
                        assembly.get("question_tokens", 0),
                        "PINNED",
                    ),
                ]

                for name, tokens, status in layers:
                    status_color = (
                        ":green[PINNED]" if status == "PINNED"
                        else ":red[DROPPED]"
                    )
                    st.markdown(
                        f"**{name}** - {tokens} tokens - {status_color}"
                    )

                st.markdown(f"**Docs used:** {assembly.get('retrieved_docs_used', 0)}")

                if budget > 0:
                    st.progress(
                        min(total_tok / budget, 1.0),
                        text=f"Token budget: {total_tok} / {budget}",
                    )

            # --- Retrieved Chunks Panel ---
            chunks = result.get("retrieved_chunks", [])
            if chunks:
                with st.expander(
                    f"Retrieved Chunks ({len(chunks)})", expanded=False
                ):
                    for idx, chunk in enumerate(chunks):
                        included = chunk.get("included_in_prompt", False)
                        icon = "+" if included else "-"
                        pii = " [PII]" if chunk.get("pii_detected") else ""
                        st.markdown(
                            f"**{icon} Chunk {idx + 1}** | "
                            f"Score: {chunk.get('score', 0):.4f} | "
                            f"Source: `{chunk.get('source', '')}` | "
                            f"Index: {chunk.get('chunk_index', 0)} | "
                            f"Tokens: {chunk.get('tokens', 0)}"
                            f"{pii}"
                        )
                        st.text(chunk.get("preview", ""))
                        if not included:
                            st.caption("(not included in prompt - budget exceeded)")
                        st.markdown("---")

        except requests.RequestException as e:
            st.error(f"RAG query failed: {e}")
