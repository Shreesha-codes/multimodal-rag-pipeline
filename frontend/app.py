import streamlit as st
import requests

st.set_page_config(page_title="Multimodal RAG", layout="wide")

st.title("Multimodal RAG")

if st.button("Check Backend Health"):
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            st.success("Backend is running: " + str(response.json()))
        else:
            st.error(f"Backend returned error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Backend is not running. Please start it on port 8000.")
