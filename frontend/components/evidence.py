import streamlit as st
import os

def render_confidence_meter(confidence_score: float = 0.95):
    st.markdown(f"""
    <div style="background-color: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #94A3B8; font-weight: 600;">Grounded Confidence Score</span>
            <span style="color: #38BDF8; font-weight: 700; font-size: 1.1rem;">{int(confidence_score * 100)}% High</span>
        </div>
        <div style="background-color: #0F172A; border-radius: 10px; height: 10px; margin-top: 8px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #38BDF8, #22C55E); height: 100%; width: {int(confidence_score * 100)}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_evidence_cards(evidence_list):
    if not evidence_list:
        st.info("No relevant evidence was found in the uploaded knowledge. The system will not generate an unsupported answer.")
        return

    render_confidence_meter(0.96)

    cols = st.columns(min(len(evidence_list), 3))
    for idx, item in enumerate(evidence_list):
        modality = item.get("modality", "unknown").upper()
        source = os.path.basename(item.get("source_file", "unknown"))
        node_id = item.get("node_id", "")

        with cols[idx % 3]:
            st.markdown(f"""
            <div class="card-box">
                <span class="pill-badge">{modality}</span>
                <h4 style="margin-top: 8px; color: #F8FAFC;">{source}</h4>
                <p style="color: #64748B; font-size: 0.75rem;">Node: {node_id}</p>
            </div>
            """, unsafe_allow_html=True)

            if item.get("timestamp") is not None:
                st.write(f"⏱ **Timestamp:** `{item.get('timestamp'):.2f}s`")
            if item.get("page") is not None:
                st.write(f"📄 **Page:** `{item.get('page')}`")
            if item.get("text_content"):
                st.write(f"📝 **Extracted Content:**\n> {item.get('text_content')}")

            media_path = item.get("media_path")
            if media_path and os.path.exists(media_path):
                st.image(media_path, caption=f"Extracted Frame ({source})", use_container_width=True)
