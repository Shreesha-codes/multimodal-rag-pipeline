"""
app.py
------
Streamlit web application for the Multimodal RAG Pipeline.
Provides a chat interface over video, audio, PDF, and image content.
"""

from __future__ import annotations

import streamlit as st

from src.models.schemas import QueryRequest
from src.retrieval.retriever import HybridRetriever
from src.retrieval.synthesis import Synthesizer
from src.storage.graph_store import GraphStore
from src.storage.vector_store import VectorStore
from src.utils.helpers import load_env, setup_logging

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

load_env()
setup_logging()

st.set_page_config(
    page_title="Multimodal RAG",
    page_icon="🔍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Component initialisation (cached)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_retriever() -> HybridRetriever:
    vs = VectorStore()
    gs = GraphStore()
    gs.load()
    return HybridRetriever(vector_store=vs, graph_store=gs)


@st.cache_resource
def get_synthesizer() -> Synthesizer:
    return Synthesizer()


retriever = get_retriever()
synthesizer = get_synthesizer()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ Settings")
    top_k = st.slider("Top-K Results", min_value=1, max_value=20, value=5)
    use_graph = st.toggle("Graph Expansion", value=True)
    st.divider()
    st.caption("Multimodal RAG Pipeline")
    st.caption("Powered by Gemini + ChromaDB + NetworkX")

# ---------------------------------------------------------------------------
# Main chat interface
# ---------------------------------------------------------------------------

st.title("🔍 Multimodal RAG — Ask Your Data")
st.caption("Ask questions over meeting recordings, architecture docs, and images.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents…"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieve and synthesise
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base…"):
            request = QueryRequest(query=prompt, top_k=top_k, use_graph=use_graph)
            hits = retriever.retrieve(request)
            response = synthesizer.synthesize(request, hits)

        st.markdown(response.answer)

        if response.sources:
            with st.expander("📚 Sources"):
                for src in response.sources:
                    st.markdown(f"- {src}")

        if response.confidence is not None:
            st.caption(f"Confidence: {response.confidence:.1%}")

    st.session_state.messages.append(
        {"role": "assistant", "content": response.answer}
    )
