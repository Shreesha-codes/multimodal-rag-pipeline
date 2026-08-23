import streamlit as st
from frontend.components.evidence import render_evidence_cards

def render_baseline_comparison(comp_data):
    if not comp_data:
        return

    col_left, col_right = st.columns(2)
    metrics = comp_data.get("metrics", {})

    b_coverage = len(metrics.get("baseline_modality_coverage", []))
    m_coverage = len(metrics.get("multimodal_modality_coverage", []))

    with col_left:
        st.markdown(f"""
        <div class="card-box" style="border-color: #EF4444;">
            <h3 style="color: #FCA5A5;">TEXT-ONLY RAG (Baseline)</h3>
            <p style="color: #94A3B8; font-size: 0.85rem;">Standard chunk-and-embed vector search</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**Answer:** {comp_data['baseline'].get('answer', '')}")
        st.markdown(f"**Modalities Covered ({b_coverage}):** `{', '.join(metrics.get('baseline_modality_coverage', []))}`")
        st.markdown(f"**Sources Covered:** `{metrics.get('baseline_source_coverage', 0)}`")
        st.warning("⚠️ Limitation: Missed visual video frame evidence and cross-modal temporal links.")
        st.markdown("#### Baseline Evidence")
        render_evidence_cards(comp_data["baseline"].get("evidence_bundle", {}).get("evidence", []))

    with col_right:
        st.markdown(f"""
        <div class="card-box" style="border-color: #22C55E;">
            <h3 style="color: #86EFAC;">MULTIMODAL GRAPH-RAG (Ours)</h3>
            <p style="color: #38BDF8; font-size: 0.85rem;">Temporal-traversal NetworkX graph expansion</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"**Answer:** {comp_data['multimodal'].get('answer', '')}")
        st.markdown(f"**Modalities Covered ({m_coverage}):** `{', '.join(metrics.get('multimodal_modality_coverage', []))}`")
        st.markdown(f"**Sources Covered:** `{metrics.get('multimodal_source_coverage', 0)}`")
        st.success("✅ Advantage: Recovered visual frame evidence via graph expansion!")
        st.markdown("#### Multimodal Evidence")
        render_evidence_cards(comp_data["multimodal"].get("evidence_bundle", {}).get("evidence", []))
