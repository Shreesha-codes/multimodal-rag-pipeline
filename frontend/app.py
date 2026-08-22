import streamlit as st
import uuid
import time
import requests
import os

st.set_page_config(page_title="Multimodal RAG", layout="wide")

API_BASE = "http://127.0.0.1:8000"

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

session_id = st.session_state.session_id

st.title("Multimodal RAG")
st.markdown("Ask questions across video, audio, images and documents with source-aware evidence.")

st.header("Upload Knowledge")
uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True)

if st.button("Process Files"):
    if not uploaded_files:
        st.warning("Please upload at least one file.")
    else:
        try:
            # 1. Upload files
            with st.spinner("Uploading files..."):
                files_payload = []
                for f in uploaded_files:
                    files_payload.append(("files", (f.name, f.getvalue(), f.type)))
                    if f.name not in st.session_state.uploaded_files:
                        st.session_state.uploaded_files.append(f.name)
                        
                upload_res = requests.post(f"{API_BASE}/upload/{session_id}", files=files_payload)
                if upload_res.status_code != 200:
                    st.error(f"Upload failed: {upload_res.text}")
                    st.stop()
                    
            # 2. Trigger processing
            process_res = requests.post(f"{API_BASE}/process/{session_id}")
            if process_res.status_code != 202:
                st.error(f"Failed to start processing: {process_res.text}")
                st.stop()
                
            # 3. Poll status
            status_container = st.empty()
            while True:
                status_res = requests.get(f"{API_BASE}/status/{session_id}")
                if status_res.status_code == 200:
                    data = status_res.json()
                    status = data.get("status", "unknown")
                    
                    with status_container.container():
                        st.write(f"**Session Status:** {status}")
                        for fname, fstatus in data.get("files", {}).items():
                            st.write(f"- **{fname}**: {fstatus}")
                            
                    if status in ["completed", "failed"]:
                        if status == "completed":
                            st.success("Processing completed successfully!")
                        else:
                            st.error("Processing failed for some files.")
                        break
                else:
                    st.error("Could not fetch status.")
                    break
                time.sleep(2)
        except requests.exceptions.ConnectionError:
            st.error("Backend is not running. Please start the Uvicorn server.")

st.header("Analyze Knowledge")
tab1, tab2, tab3 = st.tabs(["Query & Evidence", "Baseline Comparison", "Relationship Graph"])

def render_evidence(bundle):
    for item in bundle.get("evidence", []):
        with st.expander(f"{item.get('modality', 'unknown').upper()} - {item.get('source_file', 'unknown')}"):
            st.write(f"**Node ID:** {item.get('node_id')}")
            if item.get("timestamp"):
                st.write(f"**Timestamp:** {item.get('timestamp')}s")
            if item.get("page"):
                st.write(f"**Page:** {item.get('page')}")
            if item.get("text_content"):
                st.write(f"**Text/Description:** {item.get('text_content')}")
            
            media_path = item.get("media_path")
            if media_path and os.path.exists(media_path):
                st.image(media_path, caption=f"Source: {item.get('source_file')}")

with tab1:
    query = st.text_input("Ask a question about your uploaded knowledge:")
    if st.button("Ask"):
        if not query:
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing cross-modal evidence..."):
                try:
                    res = requests.get(f"{API_BASE}/query/{session_id}", params={"q": query})
                    if res.status_code == 200:
                        data = res.json()
                        st.subheader("Answer")
                        st.write(data.get("answer", ""))
                        
                        st.subheader("Cited Evidence")
                        bundle = data.get("evidence_bundle", {})
                        
                        if bundle.get("evidence"):
                            render_evidence(bundle)
                            
                        # Save bundle for relationship view
                        st.session_state.last_bundle = bundle
                    else:
                        st.error(f"Error querying backend: {res.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Backend is not running.")

with tab2:
    compare_query = st.text_input("Run comparison query:")
    if st.button("Compare"):
        if not compare_query:
            st.warning("Please enter a question.")
        else:
            with st.spinner("Running baseline and multimodal engines..."):
                try:
                    res = requests.get(f"{API_BASE}/compare/{session_id}", params={"q": compare_query})
                    if res.status_code == 200:
                        data = res.json()
                        col1, col2 = st.columns(2)
                        
                        metrics = data.get("metrics", {})
                        
                        with col1:
                            st.subheader("Text-Only Baseline")
                            st.write(data["baseline"].get("answer", ""))
                            st.write("**Modality Coverage:**", ", ".join(metrics.get("baseline_modality_coverage", [])))
                            
                            st.subheader("Baseline Evidence")
                            render_evidence(data["baseline"].get("evidence_bundle", {}))
                            
                        with col2:
                            st.subheader("Multimodal RAG")
                            st.write(data["multimodal"].get("answer", ""))
                            st.write("**Modality Coverage:**", ", ".join(metrics.get("multimodal_modality_coverage", [])))
                            
                            st.subheader("Multimodal Evidence")
                            render_evidence(data["multimodal"].get("evidence_bundle", {}))
                            
                    else:
                        st.error(f"Error comparing backend: {res.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Backend is not running.")

with tab3:
    st.subheader("Evidence Relationship Chain")
    if "last_bundle" in st.session_state:
        bundle = st.session_state.last_bundle
        evidence_list = bundle.get("evidence", [])
        
        for item in evidence_list:
            if not item.get("is_primary") and item.get("relationship_path"):
                st.markdown(f"**Primary Match** ➔ `{item.get('relationship_path')}` ➔ **{item.get('modality').upper()}** ({item.get('source_file')})")
    else:
        st.info("Run a query in the first tab to view relationships.")
