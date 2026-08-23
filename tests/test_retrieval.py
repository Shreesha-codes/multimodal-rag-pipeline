import pytest
import os
import shutil
from backend.models import MultimodalNode
from backend.services.vector_store import VectorStore
from backend.services.graph import SessionGraph
from backend.services.relationship_engine import link_temporal
from backend.services.retrieval_engine import RetrievalEngine

def test_retrieval_expansion():
    session_id = "test_retrieval_session"
    
    # Clean setup
    shutil.rmtree("chroma_db", ignore_errors=True)
    shutil.rmtree(f"graph/{session_id}", ignore_errors=True)
    
    # 1. Setup Vector Store
    vector_store = VectorStore()
    audio_node = MultimodalNode(
        id="audio_123",
        session_id=session_id,
        source_file="talk.mp4",
        modality="audio",
        timestamp=10.0,
        end_timestamp=15.0,
        text="What was discussed about database sharding?"
    )
    
    frame_node = MultimodalNode(
        id="frame_456",
        session_id=session_id,
        source_file="talk.mp4",
        modality="video_frame",
        timestamp=12.0,
        media_path="talk_12.jpg"
    )
    
    # Only adding audio to vector store so it is the ONLY primary match
    vector_store.add_nodes([audio_node])
    
    # 2. Setup Graph
    graph = SessionGraph(session_id)
    graph.add_node(audio_node)
    graph.add_node(frame_node)
    
    # Create the link
    link_temporal(graph, [audio_node, frame_node])
    graph.save()
    
    # 3. Retrieve
    engine = RetrievalEngine(session_id, vector_store)
    bundle = engine.retrieve("database sharding", top_k=1)
    
    # 4. Assertions
    assert bundle.query == "database sharding"
    assert bundle.session_id == session_id
    
    evidence_ids = {e.node_id for e in bundle.evidence}
    
    # We should have found audio directly, and frame via expansion!
    assert "audio_123" in evidence_ids
    assert "frame_456" in evidence_ids
    
    audio_ev = next(e for e in bundle.evidence if e.node_id == "audio_123")
    frame_ev = next(e for e in bundle.evidence if e.node_id == "frame_456")
    
    assert audio_ev.is_primary is True
    assert frame_ev.is_primary is False
    assert frame_ev.relationship_path == "VISIBLE_DURING"
    
    # Clean teardown
    shutil.rmtree("chroma_db", ignore_errors=True)
    shutil.rmtree(f"graph/{session_id}", ignore_errors=True)
