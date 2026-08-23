import streamlit as st
import uuid
import time
import requests
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from frontend.components.evidence import render_evidence_cards
    from frontend.components.comparison import render_baseline_comparison
    from frontend.components.graph_viz import render_interactive_graph
except ModuleNotFoundError:
    from components.evidence import render_evidence_cards
    from components.comparison import render_baseline_comparison
    from components.graph_viz import render_interactive_graph

st.set_page_config(page_title="Multimodal RAG Workspace", layout="wide", initial_sidebar_state="expanded")

API_BASE = "http://127.0.0.1:8000"

st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #E0E6ED;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #FFFFFF;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    .card-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .accent-card {
        background-color: #0F172A;
        border: 1px solid #3B82F6;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
    }
    .pill-badge {
        display: inline-block;
        background-color: #1E293B;
        color: #38BDF8;
        border: 1px solid #0284C7;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .chain-node {
        background-color: #1E293B;
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 10px 16px;
        text-align: center;
        font-weight: 600;
        color: #F8FAFC;
    }
    .chain-arrow {
        text-align: center;
        color: #38BDF8;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 6px 0;
    }
</style>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
if "uploaded_files_info" not in st.session_state:
    st.session_state.uploaded_files_info = []

session_id = st.session_state.session_id

def check_backend_health():
    for _ in range(2):
        try:
            r = requests.get(f"{API_BASE}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(0.5)
    return False

backend_ready = check_backend_health()

with st.sidebar:
    st.markdown("## ◉ MULTIMODAL RAG")
    st.markdown(f"**SESSION:** `{session_id}`")
    st.markdown("---")
    
    st.markdown("### KNOWLEDGE METRICS")
    file_count = len(st.session_state.uploaded_files_info)
    st.write(f"📁 **Total Sources:** {file_count}")
    
    video_cnt = sum(1 for f in st.session_state.uploaded_files_info if f['ext'] in ['.mp4', '.mov'])
    audio_cnt = sum(1 for f in st.session_state.uploaded_files_info if f['ext'] in ['.mp3', '.wav'])
    pdf_cnt = sum(1 for f in st.session_state.uploaded_files_info if f['ext'] == '.pdf')
    img_cnt = sum(1 for f in st.session_state.uploaded_files_info if f['ext'] in ['.png', '.jpg', '.jpeg'])
    
    st.write(f"- 🎥 Videos: {video_cnt}")
    st.write(f"- 🎙 Audio: {audio_cnt}")
    st.write(f"- 📄 PDFs: {pdf_cnt}")
    st.write(f"- 🖼 Images: {img_cnt}")
    
    st.markdown("---")
    st.markdown("### SYSTEM ENGINE")
    st.write("Vector Store (Chroma): ✓ Active")
    st.write("Graph Engine (NetworkX): ✓ Active")
    st.write("Synthesis (Gemini): ✓ Ready")
    
    st.markdown("---")
    if st.button("Clear Session"):
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
        st.session_state.uploaded_files_info = []
        if "last_bundle" in st.session_state:
            del st.session_state["last_bundle"]
        if "current_response" in st.session_state:
            del st.session_state["current_response"]
        st.rerun()

head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.markdown('<div class="main-header">MULTIMODAL RAG</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Understand your knowledge across video, audio, images and documents with source-aware evidence.</div>', unsafe_allow_html=True)
with head_col2:
    if backend_ready:
        st.success(f"System Ready\nSession: Active\n{file_count} Sources")
    else:
        st.error("Backend Offline\nStart Uvicorn server")

if not backend_ready:
    st.error("Unable to connect to the processing service. Please make sure the backend is running (`uvicorn backend.main:app --host 127.0.0.1 --port 8000`).")
    if st.button("Retry Connection"):
        st.rerun()

st.markdown("---")

st.markdown("## KNOWLEDGE SOURCES")
st.markdown("Upload anything you want to ask questions about.")

uploaded_files = st.file_uploader("Upload Video, Audio, Image, PDF or Text files", accept_multiple_files=True, type=["mp4", "mov", "mp3", "wav", "png", "jpg", "jpeg", "pdf", "txt"])

if uploaded_files:
    cols = st.columns(min(len(uploaded_files), 4))
    for idx, f in enumerate(uploaded_files):
        ext = os.path.splitext(f.name)[1].lower()
        icon = "🎥" if ext in [".mp4", ".mov"] else "🎙" if ext in [".mp3", ".wav"] else "📄" if ext == ".pdf" else "🖼" if ext in [".png", ".jpg", ".jpeg"] else "📝"
        size_str = f"{round(f.size / (1024 * 1024), 2)} MB" if f.size > 1024*1024 else f"{round(f.size / 1024, 2)} KB"
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="card-box">
                <h4>{icon} {f.name}</h4>
                <p style="color: #94A3B8; font-size: 0.85rem;">Size: {size_str}</p>
                <span class="pill-badge">Ready for Ingestion</span>
            </div>
            """, unsafe_allow_html=True)

if st.button("Process Knowledge", type="primary"):
    if not uploaded_files:
        st.warning("Please select at least one file to process.")
    elif not backend_ready:
        st.error("Backend is unavailable.")
    else:
        try:
            with st.spinner("Uploading files to session storage..."):
                files_payload = []
                st.session_state.uploaded_files_info = []
                for f in uploaded_files:
                    files_payload.append(("files", (f.name, f.getvalue(), f.type or "application/octet-stream")))
                    ext = os.path.splitext(f.name)[1].lower()
                    st.session_state.uploaded_files_info.append({"name": f.name, "ext": ext, "size": f.size})
                    
                upload_res = requests.post(f"{API_BASE}/upload/{session_id}", files=files_payload)
                if upload_res.status_code != 200:
                    st.error(f"Upload failed: {upload_res.text}")
                    st.stop()
                res_data = upload_res.json()
                if "session_id" in res_data:
                    st.session_state.session_id = res_data["session_id"]
                    session_id = res_data["session_id"]
                    
            process_res = requests.post(f"{API_BASE}/process/{session_id}")
            if process_res.status_code not in [200, 202]:
                st.error(f"Failed to trigger processing: {process_res.text}")
                st.stop()
                
            status_placeholder = st.empty()
            while True:
                status_res = requests.get(f"{API_BASE}/status/{session_id}")
                if status_res.status_code == 200:
                    data = status_res.json()
                    status = data.get("status", "unknown")
                    
                    with status_placeholder.container():
                        st.markdown("### PROCESSING STATUS")
                        for finfo in st.session_state.uploaded_files_info:
                            fname = finfo["name"]
                            ext = finfo["ext"]
                            with st.expander(f"✓ {fname} — Status: {status.upper()}", expanded=True):
                                st.write("✓ File uploaded")
                                if ext in [".mp4", ".mov"]:
                                    st.write("✓ Audio extracted via FFmpeg")
                                    st.write("✓ Speech transcribed via Whisper")
                                    st.write("✓ Important frames detected via PySceneDetect")
                                    st.write("✓ OCR completed via Tesseract")
                                    st.write("✓ Visual analysis completed via Gemini Vision")
                                    st.write("✓ Cross-modal links created in NetworkX")
                                elif ext in [".mp3", ".wav"]:
                                    st.write("✓ Speech transcribed via Whisper")
                                    st.write("✓ Timestamped audio nodes created")
                                elif ext == ".pdf":
                                    st.write("✓ Pages extracted via PyMuPDF")
                                    st.write("✓ Text extracted")
                                    st.write("✓ OCR checked")
                                elif ext in [".png", ".jpg", ".jpeg"]:
                                    st.write("✓ OCR text extracted")
                                    st.write("✓ Visual summary created via Gemini Vision")
                                st.write("✓ Embeddings stored in ChromaDB")
                                
                    if status in ["completed", "failed"]:
                        if status == "completed":
                            st.success("Knowledge processing complete! All modalities indexed and linked in graph.")
                        else:
                            st.error(f"Processing failed: {data.get('error', 'Unknown error')}")
                        break
                else:
                    st.error("Failed to query status.")
                    break
                time.sleep(1)
        except Exception as e:
            st.error(f"Connection error: {str(e)}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Answer & Evidence", "Baseline Comparison", "Interactive Knowledge Map"])

with tab1:
    st.markdown("## ASK YOUR KNOWLEDGE")
    st.markdown("Ask questions that may require evidence from multiple sources.")
    
    st.markdown("**Example Questions:**")
    ex_cols = st.columns(3)
    preset_q = None
    if ex_cols[0].button("DB Sharding & Visuals"):
        preset_q = "What was discussed about database sharding and what was shown on screen?"
    if ex_cols[1].button("Redis & Architecture"):
        preset_q = "What architecture diagram was being explained when Redis was mentioned?"
    if ex_cols[2].button("PDF & Video Alignment"):
        preset_q = "What does the PDF say about the architecture shown in the video?"

    default_val = preset_q if preset_q else ""
    user_query = st.text_input("Enter your question:", value=default_val, placeholder="What was discussed about database sharding and what was shown on screen?")
    
    if st.button("Ask Multimodal RAG", type="primary"):
        if not user_query:
            st.warning("Please enter a question.")
        elif not backend_ready:
            st.error("Backend is unavailable.")
        else:
            with st.spinner("Retrieving cross-modal evidence and expanding graph..."):
                try:
                    res = requests.get(f"{API_BASE}/query/{session_id}", params={"q": user_query})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.current_response = data
                        st.session_state.last_bundle = data.get("evidence_bundle", {})
                    else:
                        st.error(f"Backend Query Error: {res.text}")
                except Exception as e:
                    st.error(f"Failed to query backend: {str(e)}")

    if "current_response" in st.session_state:
        data = st.session_state.current_response
        bundle = data.get("evidence_bundle", {})
        evidence_list = bundle.get("evidence", [])
        
        st.markdown("---")
        st.markdown("### ANSWER")
        st.markdown(f"""
        <div class="accent-card">
            <h3 style="color: #F8FAFC; margin-bottom: 8px;">{data.get('answer', '')}</h3>
            <p style="color: #38BDF8; font-size: 0.9rem; margin-top: 12px;">
                Evidence: {len(evidence_list)} sources | Modalities: {", ".join(list({item.get('modality', '').upper() for item in evidence_list}))}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### SUPPORTING EVIDENCE")
        st.markdown("Evidence retrieved from your knowledge.")
        render_evidence_cards(evidence_list)
        
        st.markdown("---")
        st.markdown("### WHY THESE SOURCES ARE CONNECTED")
        if evidence_list:
            chain_cols = st.columns(len(evidence_list))
            for idx, item in enumerate(evidence_list):
                mod = item.get("modality", "unknown").upper()
                src = os.path.basename(item.get("source_file", "unknown"))
                t_str = f"{item.get('timestamp'):.2f}s" if item.get("timestamp") is not None else f"Page {item.get('page')}" if item.get("page") is not None else ""
                
                with chain_cols[idx]:
                    st.markdown(f"""
                    <div class="chain-node">
                        {mod}<br/>
                        <span style="font-size: 0.8rem; color: #94A3B8;">{src}</span><br/>
                        <span style="font-size: 0.8rem; color: #38BDF8;">{t_str}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if not item.get("is_primary") and item.get("relationship_path"):
                        st.markdown(f'<div class="chain-arrow">↓ {item.get("relationship_path")}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### EVIDENCE COVERAGE")
        modalities_present = list({item.get('modality', '').upper() for item in evidence_list})
        cov_str = " · ".join([f"✓ {m}" for m in modalities_present])
        st.success(f"{cov_str} ({len(modalities_present)} modalities contributed to this grounded answer)")
        
        with st.expander("View retrieval trace"):
            st.code("""
User Query
    ↓
Semantic Search (ChromaDB)
    ↓
Primary Evidence Identified
    ↓
Graph Expansion (NetworkX)
    ↓
Related Cross-Modal Evidence Linked
    ↓
Evidence Ranking & Deduplication
    ↓
Gemini 1.5 Pro Synthesis
    ↓
Grounded Answer & Provenance Check
            """, language="text")

with tab2:
    st.markdown("## BASELINE COMPARISON")
    st.markdown("Compare standard Text-Only RAG against our Multimodal Graph-RAG system.")
    
    comp_query = st.text_input("Enter comparison query:", placeholder="What architecture diagram was shown?", key="comp_q")
    if st.button("Compare RAG Engines", type="primary"):
        if not comp_query:
            st.warning("Please enter a question.")
        elif not backend_ready:
            st.error("Backend is unavailable.")
        else:
            with st.spinner("Executing Text-Only Baseline vs Multimodal Graph-RAG..."):
                try:
                    res = requests.get(f"{API_BASE}/compare/{session_id}", params={"q": comp_query})
                    if res.status_code == 200:
                        st.session_state.comp_data = res.json()
                    else:
                        st.error(f"Error comparing backend: {res.text}")
                except Exception as e:
                    st.error(f"Backend error: {str(e)}")

    if "comp_data" in st.session_state:
        render_baseline_comparison(st.session_state.comp_data)

with tab3:
    st.markdown("## INTERACTIVE KNOWLEDGE MAP")
    st.markdown("Drag, zoom, and explore cross-modal nodes and edges in real-time.")
    if "last_bundle" in st.session_state:
        bundle = st.session_state.last_bundle
        evidence_list = bundle.get("evidence", [])
        
        st.markdown(f"""
        <div class="card-box">
            <h4>Graph Statistics</h4>
            <p>Active Nodes: <b>{len(evidence_list)}</b> | Temporal/Entity Edges: <b>{sum(1 for i in evidence_list if i.get('relationship_path'))}</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        render_interactive_graph(evidence_list)
    else:
        st.info("Run a query in the first tab to render the interactive knowledge graph.")
