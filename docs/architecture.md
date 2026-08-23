# Multimodal RAG Pipeline: System Architecture

## System Overview
The Multimodal RAG Pipeline is a sophisticated backend engine designed to process multiple file types (videos, audio, PDFs, images) simultaneously, extracting deep structured meaning from each, and mapping those meanings into a traversable mathematical graph. 

It upgrades traditional "Text-Only RAG" by fundamentally linking text transcripts with visual diagrams and temporal context, enabling an LLM to accurately deduce relationships across completely different modalities.

## Data Flow
1. **Upload & Session Management:** A user session is instantiated. Files are streamed chunk-by-chunk to the FastAPI backend, isolated inside a `session_id` directory to prevent cross-contamination.
2. **Parallel Ingestion:**
   - **Video:** Split into audio tracks (via `ffmpeg`) and representative visual frames (via `PySceneDetect`).
   - **Audio:** Transcribed into heavily timestamped segments using `faster-whisper`.
   - **Images & PDFs:** Parsed for structural textual content (`pypdf`, `pytesseract` OCR) and visual summaries (`Gemini Vision`).
3. **Graph Assembly:** The extracted entities are mapped into standard `MultimodalNode` structures. `NetworkX` iterates through these nodes, binding them together (e.g. mapping an audio timestamp to a video frame timestamp).
4. **Vector Embedding:** Nodes are embedded into a dense semantic space using `ChromaDB` and `sentence-transformers`.
5. **Cross-Modal Retrieval:** When a user queries the system, `ChromaDB` fetches the most relevant initial text. Crucially, the system then performs *Graph Expansion*, walking the `NetworkX` edges to pull in temporally or semantically related video frames and diagrams.
6. **LLM Synthesis:** The full `EvidenceBundle` is passed to the LLM (Gemini 1.5 Pro) with strict instructions to answer *only* based on the retrieved evidence. The backend intercepts the LLM citations and forcibly injects true provenance metadata (timestamps, page numbers) to strictly eliminate hallucination.

## Node Schema
Every extracted data point is preserved as a structured `MultimodalNode`:
```json
{
  "id": "node_123",
  "session_id": "session_abc",
  "modality": "video_frame",
  "source_file": "presentation.mp4",
  "timestamp": 12.5,
  "media_path": "storage/processed/session_abc/frames/frame_12.jpg",
  "text": "Extracted OCR or visual summary",
  "entities": ["Database", "Architecture"]
}
```

## Relationship Model
The system enforces strict directional links:
- `VISIBLE_DURING`: Links an `audio` transcript node to a `video_frame` node if the frame was on screen while the words were spoken.
- `RELATED_TO`: Links nodes that share high-confidence semantic entities.

## Baseline Architecture
To objectively prove the utility of the graph expansion, the architecture runs a strict dual-track system:
- **Multimodal Engine:** Traverses the graph.
- **Baseline Engine:** Reads only the raw text strings ingested into a separate, isolated `baseline_collection` in ChromaDB. It skips the `NetworkX` graph entirely.

## Key Design Decisions
1. **Deterministic Provenance:** The LLM is banned from generating its own timestamps or citations. The backend maps the LLM's cited `node_id` back to the original `MultimodalNode` database, guaranteeing the frontend receives 100% accurate file sources and timestamps.
2. **Session Isolation:** All processing, graph serialization, and vector querying forcefully require a `session_id`. It is mathematically impossible for Session A to retrieve vectors from Session B.
3. **No Heavy Image Embeddings:** To maintain performance on consumer hardware during the hackathon, we opted against `OpenCLIP` tensor models. Instead, we generate robust text-based visual summaries of images using Gemini Vision, and embed those textual summaries. This achieves multimodal semantic retrieval at a fraction of the compute cost.

## Limitations & Future Improvements
1. **Model Cold Starts:** `faster-whisper` and `sentence-transformers` download significant tensor weights on their first run.
2. **Complex Scene Detection:** `PySceneDetect` uses thresholding. Highly dynamic videos (like fast-moving sports) could overwhelm the frame-extractor, leading to API quota issues with Gemini Vision. Future versions should implement a strictly capped frame-sampling rate fallback.
3. **OpenCLIP Integration:** A future phase should re-introduce native CLIP embeddings for pure image-to-image semantic matching without relying on LLM-generated visual descriptions.
