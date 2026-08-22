# 🔍 Multimodal RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) system that ingests and reasons over **videos, audio transcripts, PDFs, and images** using Google Gemini, ChromaDB, and a NetworkX knowledge graph.

---

## 📁 Project Structure

```
multimodal-rag/
├── app.py                      # Streamlit chat UI
├── run_pipeline.py             # Ingestion CLI script
├── requirements.txt
├── .env                        # API keys (not committed)
│
├── src/
│   ├── models/
│   │   └── schemas.py          # Pydantic data models
│   ├── ingestion/
│   │   ├── video_extractor.py  # OpenCV frame extraction
│   │   ├── audio_extractor.py  # moviepy + Whisper transcription
│   │   ├── doc_extractor.py    # PyMuPDF PDF parsing
│   │   └── vision_analyzer.py  # Gemini Vision image descriptions
│   ├── storage/
│   │   ├── vector_store.py     # ChromaDB semantic index
│   │   ├── graph_store.py      # NetworkX evidence graph
│   │   └── aligner.py          # Cross-modal alignment
│   ├── retrieval/
│   │   ├── retriever.py        # Hybrid vector + graph retrieval
│   │   ├── baseline_rag.py     # Vector-only baseline
│   │   └── synthesis.py        # LLM answer synthesis
│   └── utils/
│       └── helpers.py          # Logging, file discovery, timing
│
├── data/
│   ├── raw/                    # Drop input files here
│   └── processed/              # Auto-generated (audio, frames, pdf_images)
├── chroma_db/                  # ChromaDB persistent storage
└── graph/
    └── evidence_graph.json     # Serialised knowledge graph
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

Edit `.env`:
```
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. Add your raw files

Place files in `data/raw/`:
- `*.mp4 / *.mov` — meeting recordings
- `*.pdf` — documents
- `*.png / *.jpg` — images / diagrams

### 4. Run ingestion

```bash
python run_pipeline.py
```

**Optional flags:**
```bash
python run_pipeline.py --skip-video    # skip frame extraction
python run_pipeline.py --skip-audio    # skip Whisper transcription
python run_pipeline.py --skip-vision   # skip Gemini vision analysis
```

### 5. Launch the chat app

```bash
streamlit run app.py
```

---

## 🧠 Architecture

```
Raw Files (video / audio / PDF / image)
         │
         ▼
    ┌─────────────────────────────────────┐
    │          Ingestion Layer            │
    │  VideoExtractor  →  VisionAnalyzer  │
    │  AudioExtractor  →  Whisper ASR     │
    │  DocExtractor    →  PyMuPDF         │
    └──────────────┬──────────────────────┘
                   │  Chunks (text + metadata)
                   ▼
    ┌─────────────────────────────────────┐
    │           Storage Layer             │
    │  VectorStore (ChromaDB + Gemini     │
    │               embeddings)           │
    │  GraphStore  (NetworkX + JSON)      │
    │  Aligner     (cross-modal edges)    │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │          Retrieval Layer            │
    │  HybridRetriever                    │
    │    Stage 1: Vector similarity       │
    │    Stage 2: Graph expansion         │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │         Synthesis Layer             │
    │  Synthesizer → Gemini 1.5 Pro       │
    │  (grounded, cited answer)           │
    └─────────────────────────────────────┘
```

---

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | **Required.** Google AI Studio API key |
| `GEMINI_LLM_MODEL` | `gemini-1.5-pro` | LLM for synthesis |
| `GEMINI_EMBED_MODEL` | `text-embedding-004` | Embedding model |
| `WHISPER_MODEL` | `base` | Whisper model size (tiny/base/small/medium/large) |

---

## 📦 Key Dependencies

| Library | Purpose |
|---|---|
| `google-generativeai` | Gemini LLM + embeddings |
| `chromadb` | Vector store |
| `networkx` | Knowledge graph |
| `pydantic` | Data validation |
| `PyMuPDF` | PDF text + image extraction |
| `opencv-python` | Video frame extraction |
| `moviepy` | Audio extraction from video |
| `openai-whisper` | Speech-to-text transcription |
| `streamlit` | Web UI |