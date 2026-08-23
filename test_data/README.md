# Multimodal RAG Benchmark Test Dataset

This directory contains the canonical demonstration dataset for the Multimodal Graph-RAG system.

## File Inventory & Modalities

| Modality | File Path | Content Overview |
| :--- | :--- | :--- |
| **Video** | `video/architecture_meeting.mp4` | Video clip containing synthesized spoken explanation and visible visual frames. |
| **Audio** | `audio/architecture_audio.mp3` | Spoken audio explanation of database sharding and caching. |
| **Document** | `documents/architecture.pdf` | Technical documentation explaining database sharding, horizontal partitioning, and Redis lookup layer. |
| **Image** | `images/architecture_diagram.png` | Architecture diagram image titled "ARCHITECTURE DIAGRAM: DB SHARDING & REDIS LAYER". |
| **Text** | `text/meeting_notes.txt` | Text summary notes regarding partition write scalability. |

## Expected Relationship Graph Model

```
Audio Transcript (architecture_audio.mp3 | 0-10s)
       │
       │ VISIBLE_DURING
       ▼
Video Frame (architecture_meeting.mp4 | 0s-10s)
       │
       │ RELATED_TO (shared entity: Database Sharding / Redis)
       ▼
PDF Document (architecture.pdf | Page 1)
       │
       │ RELATED_TO (shared entity: Architecture Diagram)
       ▼
Diagram Image (architecture_diagram.png)
```

## 4 Canonical Demo Questions

1. **"What was discussed about database sharding and what was shown on screen?"**
   - *Expected Evidence:* Audio transcript (`architecture_audio.mp3`), Video Frame (`architecture_meeting.mp4`), PDF Document (`architecture.pdf`).

2. **"What architecture diagram was being explained when Redis was mentioned?"**
   - *Expected Evidence:* Video Frame (`architecture_meeting.mp4`), Image Diagram (`architecture_diagram.png`).

3. **"What does the PDF say about the architecture shown in the video?"**
   - *Expected Evidence:* Video Frame (`architecture_meeting.mp4`), PDF Page 1 (`architecture.pdf`).

4. **"What did the speaker say about Kubernetes cluster setup?"**
   - *Expected Evidence:* None (Anti-hallucination test; the system safely returns `confidence="none"` or `"No relevant evidence found"`).
