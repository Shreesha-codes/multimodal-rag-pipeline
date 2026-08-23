# Relationship-Aware Multimodal Graph-RAG Pipeline

A production-grade, source-grounded Multimodal RAG system that ingests **Video, Audio, Images, PDFs, and Text**, extracts structured nodes across modalities, builds cross-modal temporal and entity relationship graphs, and performs relationship-aware retrieval to answer complex queries with verifiable provenance.

---

## Key Features

1. **True Multimodal Ingestion**
   - **Video:** Extract audio with FFmpeg, detect scene changes with PySceneDetect, run OCR with Tesseract, and analyze key visual frames with Gemini Vision.
   - **Audio:** Transcribe speech with timestamps using `faster-whisper`.
   - **PDF & Images:** Extract text with PyMuPDF, run OCR, and extract visual concepts.
   - **Text:** Direct semantic chunking.

2. **Cross-Modal Relationship Graph (NetworkX)**
   - Automatically builds directional edges between modalities:
     - `VISIBLE_DURING`: Connects audio spoken segments to key video frames appearing at the same timestamp (`t_audio - 2s <= t_frame <= t_audio + 2s`).
     - `RELATED_TO`: Connects nodes sharing visual or textual entities across PDFs, Images, and Video frames.

3. **Relationship-Aware Graph Expansion**
   - Combines vector search in ChromaDB with NetworkX graph expansion.
   - When vector search hits an audio transcript, graph expansion traverses `VISIBLE_DURING` edges to retrieve the exact frame shown on screen during that segment.

4. **Verifiable Backend Provenance**
   - Discards LLM-invented citations and enforces backend metadata (node ID, source filename, timestamp, page number, media path).

5. **Text-Only Baseline RAG Comparison**
   - Includes an isolated text-only vector collection for head-to-head comparison demonstrating evidence recovered by Multimodal Graph-RAG that standard RAG loses.

6. **Interactive 2D Knowledge Graph UI**
   - Built with Streamlit and `vis-network` JS HTML components for interactive node dragging and zoom.

---

## Project Structure

```
multimodal-rag-pipeline/
├── backend/
│   ├── main.py                # FastAPI entrypoint with lifespan context
│   ├── models.py              # MultimodalNode & Evidence schemas
│   ├── config.py              # Configuration & dependency check
│   ├── routes/                # Health, Upload, Process, Query, Compare APIs
│   └── services/              # Modality processors, Graph, VectorStore, Gemini
├── frontend/
│   ├── app.py                 # Streamlit main workspace
│   └── components/            # Evidence cards, Comparison, Interactive Graph
├── storage/                   # Session uploads & processed frames (gitignored)
├── chroma_db/                 # Persistent ChromaDB collections (gitignored)
├── graph/                     # Persisted NetworkX graphs (gitignored)
├── test_data/                 # Committed reproducible demo dataset
│   ├── README.md              # Test dataset documentation
│   ├── video/
│   ├── audio/
│   ├── images/
│   ├── documents/
│   └── text/
├── scripts/
│   ├── build_test_dataset.py  # Test dataset generator
│   └── validate_demo.py       # Automated E2E demo validator
├── tests/                     # Pytest suite (8 unit tests + E2E)
├── docs/
│   └── architecture.md        # Detailed system architecture document
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Prerequisites

1. **System Dependencies:**
   - **Python 3.10+**
   - **FFmpeg** (Ensure `ffmpeg` is in your system PATH)
   - **Tesseract OCR** (Ensure `tesseract` is installed)

2. **Environment Setup:**
   Copy `.env.example` to `.env` and provide your Google Gemini API key:
   ```bash
   GOOGLE_API_KEY="your-gemini-api-key"
   ```

---

## Installation & Setup

1. **Activate Virtual Environment & Install Dependencies:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Generate Test Dataset (Optional):**
   ```powershell
   python scripts/build_test_dataset.py
   ```

---

## Running the Application

### 1. Start FastAPI Backend
```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 2. Start Streamlit Frontend
```powershell
streamlit run frontend/app.py
```

Open browser to `http://localhost:8501`.

---

## Demo Questions & Expected Evidence

| # | Demo Question | Expected Retrieved Evidence |
| :- | :--- | :--- |
| **1** | *"What was discussed about database sharding and what was shown on screen?"* | Audio transcript (`architecture_audio.mp3`), Video Frame (`architecture_meeting.mp4`), PDF (`architecture.pdf`). |
| **2** | *"What architecture diagram was being explained when Redis was mentioned?"* | Video Frame (`architecture_meeting.mp4`), Image Diagram (`architecture_diagram.png`). |
| **3** | *"What does the PDF say about the architecture shown in the video?"* | Video Frame (`architecture_meeting.mp4`), PDF Page 1 (`architecture.pdf`). |
| **4** | *"What did the speaker say about Kubernetes cluster setup?"* | Anti-hallucination check (Returns no false evidence, safely indicating ungrounded request). |

---

## Automated Validation & Testing

Run the automated end-to-end demo validation script:
```powershell
$env:PYTHONPATH="."
python scripts/validate_demo.py
```

Run unit tests:
```powershell
pytest tests/ -v
```
