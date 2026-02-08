"""RAG Operator Console - extends Phase 1 Streamlit design."""
import os
import time
import glob as glob_module

import streamlit as st
import requests

st.set_page_config(page_title="RAG Operator Console", layout="wide")
st.title("RAG Operator Console")

API_URL = os.getenv("API_URL", "http://localhost:8080")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

AVAILABLE_MODELS = [
    {"id": "gemma2:2b", "size": "1.6GB", "tier": "fast"},
    {"id": "llama3.2:1b", "size": "1.3GB", "tier": "fast"},
    {"id": "llama3.2:3b", "size": "2.0GB", "tier": "balanced"},
    {"id": "phi3:3.8b", "size": "2.2GB", "tier": "balanced"},
    {"id": "mistral:7b", "size": "4.4GB", "tier": "quality"},
    {"id": "llama3.1:8b", "size": "4.9GB", "tier": "quality"},
]

MODEL_OPTIONS = [m["id"] for m in AVAILABLE_MODELS]

# -------------------------------------------------------------------------
# Sidebar: Model selection + Parameters + Document Management + Status
# -------------------------------------------------------------------------
with st.sidebar:
    st.header("Model Selection")
    selected_model = st.selectbox("Active Model", MODEL_OPTIONS, index=2)
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

    try:
        ollama_resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        color = "green" if ollama_resp.status_code == 200 else "red"
        status = "connected" if ollama_resp.status_code == 200 else "unreachable"
        st.markdown(f"Ollama: :{color}[{status}]")
    except requests.RequestException:
        st.markdown("Ollama: :red[unreachable]")

# -------------------------------------------------------------------------
# Main area: tabs for Generate, Compare, RAG Query
# -------------------------------------------------------------------------
tab_generate, tab_compare, tab_rag = st.tabs(
    ["Generate", "Compare Models", "RAG Query"]
)

# --- Generate Tab (Phase 1 carry-forward) ---
with tab_generate:
    prompt = st.text_area("Enter your prompt:", height=150, key="gen_prompt")
    if st.button("Generate", type="primary", disabled=not prompt, key="gen_btn"):
        with st.spinner(f"Generating with {selected_model}..."):
            try:
                resp = requests.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={
                        "model": selected_model,
                        "prompt": prompt,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                        "stream": False,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()
                st.markdown("### Response")
                st.write(result.get("response", ""))
                eval_count = result.get("eval_count", 0)
                eval_dur = result.get("eval_duration", 0)
                latency_ms = round(eval_dur / 1e6, 1) if eval_dur else 0
                st.caption(
                    f"Model: {selected_model} | "
                    f"Latency: {latency_ms}ms | "
                    f"Tokens: {eval_count}"
                )
            except requests.RequestException as e:
                st.error(f"Generation failed: {e}")

# --- Compare Tab (Phase 1 carry-forward) ---
with tab_compare:
    compare_prompt = st.text_area(
        "Enter your prompt:", height=150, key="cmp_prompt"
    )
    compare_models = st.multiselect(
        "Select models to compare",
        MODEL_OPTIONS,
        default=["llama3.2:3b", "mistral:7b"],
    )
    if st.button("Compare", type="primary", disabled=not compare_prompt, key="cmp_btn"):
        if len(compare_models) < 2:
            st.warning("Select at least 2 models to compare.")
        else:
            cols = st.columns(len(compare_models))
            for col, model_id in zip(cols, compare_models):
                with col:
                    st.markdown(f"### {model_id}")
                    with st.spinner(f"Generating with {model_id}..."):
                        try:
                            resp = requests.post(
                                f"{OLLAMA_HOST}/api/generate",
                                json={
                                    "model": model_id,
                                    "prompt": compare_prompt,
                                    "options": {
                                        "temperature": temperature,
                                        "num_predict": max_tokens,
                                    },
                                    "stream": False,
                                },
                                timeout=120,
                            )
                            resp.raise_for_status()
                            result = resp.json()
                            st.write(result.get("response", ""))
                            eval_count = result.get("eval_count", 0)
                            eval_dur = result.get("eval_duration", 0)
                            latency_ms = round(eval_dur / 1e6, 1) if eval_dur else 0
                            st.caption(
                                f"Latency: {latency_ms}ms | Tokens: {eval_count}"
                            )
                        except requests.RequestException as e:
                            st.error(f"Failed: {e}")

# --- RAG Query Tab (Phase 2 centerpiece) ---
with tab_rag:
    rag_query = st.text_area(
        "Enter your question:", height=150, key="rag_prompt"
    )

    if st.button("Query RAG", type="primary", disabled=not rag_query, key="rag_btn"):
        with st.spinner(f"Querying RAG pipeline with {selected_model}..."):
            try:
                resp = requests.post(
                    f"{API_URL}/query",
                    json={
                        "query": rag_query,
                        "model": selected_model,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()

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
