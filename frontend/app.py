import streamlit as st
import requests

st.set_page_config(page_title="Multimodal RAG", layout="wide")

st.title("Multimodal RAG - Upload")

st.write("Upload files to start a new processing session.")
st.write("Supported formats: MP4, MOV, MP3, WAV, PNG, JPG, JPEG, PDF, TXT")

uploaded_files = st.file_uploader(
    "Select files",
    accept_multiple_files=True,
    type=["mp4", "mov", "mp3", "wav", "png", "jpg", "jpeg", "pdf", "txt"]
)

if uploaded_files:
    st.write("Selected files:")
    for f in uploaded_files:
        st.write(f"- {f.name} ({f.size / 1024:.2f} KB)")
        
    if st.button("Upload and Process"):
        files = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
        
        with st.spinner("Uploading..."):
            try:
                response = requests.post("http://localhost:8000/upload", files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data["session_id"]
                    st.success(f"Upload successful! Session ID: {session_id}")
                    
                    st.subheader("File Status")
                    for file_info in data["files"]:
                        st.write(f"**{file_info['original_filename']}**: {file_info['processing_status']}")
                else:
                    st.error(f"Upload failed: {response.json().get('detail', response.text)}")
            except requests.exceptions.ConnectionError:
                st.error("Backend is not running. Please start it on port 8000.")
