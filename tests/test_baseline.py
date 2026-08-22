import pytest
import os
import shutil
from backend.models import MultimodalNode
from backend.services.vector_store import VectorStore
from backend.services.graph import SessionGraph
from backend.services.relationship_engine import link_temporal
from backend.services.baseline_engine import BaselineEngine

def test_baseline_isolation():
    session_id = "test_baseline_session"
    
    shutil.rmtree("chroma_db", ignore_errors=True)
    shutil.rmtree(f"graph/{session_id}", ignore_errors=True)
    
    vector_store = VectorStore()
    
    # 1. Create an audio node that directly matches the text query
    audio_node = MultimodalNode(
        id="audio_abc",
        session_id=session_id,
        source_file="talk.mp4",
        modality="audio",
        timestamp=10.0,
        end_timestamp=15.0,
        text="What was discussed about database sharding?"
    )
    
    # 2. Create a frame node that is temporally linked but doesn't have matching text
    frame_node = MultimodalNode(
        id="frame_xyz",
        session_id=session_id,
        source_file="talk.mp4",
        modality="video_frame",
        timestamp=12.0,
        media_path="talk_12.jpg",
        text="[Diagram of a database]"
    )
    
    # Add to BOTH regular and baseline collections
    nodes = [audio_node, frame_node]
    vector_store.add_nodes(nodes)
    vector_store.add_baseline_nodes(nodes)
    
    # Setup graph linking them
    graph = SessionGraph(session_id)
    graph.add_node(audio_node)
    graph.add_node(frame_node)
    link_temporal(graph, nodes)
    graph.save()
    
    # 3. Test Baseline Engine
    # We mock generate_answer just to inspect the bundle easily
    baseline_engine = BaselineEngine(session_id, vector_store)
    
    # Hack the generator to just return the bundle to avoid LLM call in test
    import backend.services.baseline_engine as be
    original_generate = be.generate_answer
    
    class MockFinalResponse:
        def __init__(self, bundle):
            self.evidence_bundle = bundle
            
    be.generate_answer = lambda q, b: MockFinalResponse(b)
    
    try:
        baseline_response = baseline_engine.retrieve_and_answer("What was discussed about database sharding?", top_k=1)
        evidence = baseline_response.evidence_bundle.evidence
        
        # PROOF: Baseline only retrieved the text chunk, NO graph expansion
        assert len(evidence) == 1
        assert evidence[0].node_id == "audio_abc"
    finally:
        be.generate_answer = original_generate
        shutil.rmtree("chroma_db", ignore_errors=True)
        shutil.rmtree(f"graph/{session_id}", ignore_errors=True)
