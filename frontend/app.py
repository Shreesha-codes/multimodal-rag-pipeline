import time
import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Multimodal RAG Pipeline", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .node-card { background: #1e1e2e; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; border-left: 3px solid #7c3aed; }
    .pipeline-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .badge-video { background: #7c3aed22; color: #a78bfa; }
    .badge-audio { background: #059669 22; color: #6ee7b7; }
    .badge-image { background: #db277722; color: #f9a8d4; }
    .badge-pdf   { background: #d9770622; color: #fcd34d; }
    .badge-text  { background: #0284c722; color: #7dd3fc; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Multimodal RAG Pipeline")
st.write("Upload files from any modality — video, audio, image, PDF, or plain text — and process them into structured nodes.")

SUPPORTED = ["mp4", "mov", "mp3", "wav", "png", "jpg", "jpeg", "pdf", "txt"]
uploaded_files = st.file_uploader(
    "Select files (MP4, MOV, MP3, WAV, PNG, JPG, JPEG, PDF, TXT)",
    accept_multiple_files=True,
    type=SUPPORTED,
)

MODALITY_ICONS = {
    "video": "🎬",
    "audio": "🎵",
    "image": "🖼️",
    "pdf": "📄",
    "text": "📝",
    "unknown": "❓",
}

if uploaded_files:
    st.markdown("### 📁 Selected Files")
    for f in uploaded_files:
        st.write(f"- **{f.name}** — {f.size / 1024:.1f} KB")

    if st.button("⬆️ Upload & Process", type="primary"):
        files = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in uploaded_files]

        session_id = None
        with st.spinner("Uploading files…"):
            try:
                resp = requests.post(f"{BASE_URL}/upload", files=files, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    session_id = data["session_id"]
                    st.success(f"✅ Upload successful — Session: `{session_id}`")
                else:
                    st.error(f"Upload failed: {resp.json().get('detail', resp.text)}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Backend is not reachable on port 8000. Please start it first.")

        if session_id:
            with st.spinner("Processing…"):
                try:
                    proc_resp = requests.post(f"{BASE_URL}/process/{session_id}", timeout=30)
                    if proc_resp.status_code != 200:
                        st.error(f"Failed to start processing: {proc_resp.text}")
                        st.stop()
                except requests.exceptions.ConnectionError:
                    st.error("❌ Backend connection lost during processing trigger.")
                    st.stop()

                results = None
                for _ in range(120):
                    time.sleep(2)
                    try:
                        r = requests.get(f"{BASE_URL}/process/results/{session_id}", timeout=10)
                        if r.status_code == 200:
                            data = r.json()
                            if data.get("status") == "complete":
                                results = data
                                break
                    except Exception:
                        pass

            if results:
                st.markdown("---")
                st.markdown("### 🔍 Processing Results")

                total_nodes = results.get("total_nodes", 0)
                file_results = results.get("files", [])
                st.metric("Total Nodes Extracted", total_nodes)

                for file_result in file_results:
                    pipeline = file_result.get("pipeline", "unknown")
                    icon = MODALITY_ICONS.get(pipeline, "❓")
                    fname = file_result.get("file_path", "").split("/")[-1].split("\\")[-1]
                    node_count = file_result.get("node_count", 0)
                    errors = file_result.get("errors", [])

                    with st.expander(f"{icon} **{fname}** — `{pipeline}` pipeline — {node_count} nodes", expanded=True):
                        if errors:
                            for err in errors:
                                st.warning(f"⚠️ {err}")

                        nodes = file_result.get("nodes", [])
                        for node in nodes[:10]:
                            modality = node.get("modality", "")
                            text = node.get("text") or ""
                            media = node.get("media_path") or ""
                            page = node.get("page_number")
                            prov = node.get("provenance", "")

                            label = f"`{modality}`"
                            if page:
                                label += f" · page {page}"
                            if text:
                                preview = text[:200].replace("\n", " ")
                                st.markdown(f"**{label}** — {preview}{'…' if len(text) > 200 else ''}")
                            elif media:
                                st.markdown(f"**{label}** — `{media}`")
                            else:
                                st.markdown(f"**{label}** — *(no text or media)*")

                        if len(nodes) > 10:
                            st.caption(f"…and {len(nodes) - 10} more nodes not shown.")
            else:
                st.warning("⏳ Processing is taking longer than expected. Check the backend logs.")
