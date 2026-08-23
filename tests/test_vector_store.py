import pytest
import os
import shutil
from backend.models import MultimodalNode
from backend.services.vector_store import VectorStore

def test_vector_store_operations():
    test_db_dir = "chroma_db"
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir, ignore_errors=True)
        
    store = VectorStore()
    
    session_a = "session_A"
    session_b = "session_B"
    
    node1 = MultimodalNode(
        id="n1", session_id=session_a, source_file="doc.pdf", modality="pdf_text", text="The capital of France is Paris."
    )
    node2 = MultimodalNode(
        id="n2", session_id=session_a, source_file="doc.pdf", modality="pdf_text", text="Water boils at 100 degrees."
    )
    node3 = MultimodalNode(
        id="n3", session_id=session_b, source_file="doc.pdf", modality="pdf_text", text="The capital of France is Paris."
    )
    
    store.add_nodes([node1, node2, node3])
    
    # Verify search and cross-session isolation
    results_a = store.query_text("What is the capital of France?", session_a)
    
    assert len(results_a) > 0
    
    # Must only retrieve nodes from session_a
    for res in results_a:
        assert res["metadata"]["session_id"] == session_a
        
    assert results_a[0]["id"] == "n1"
    
    results_b = store.query_text("What is the capital of France?", session_b)
    assert len(results_b) > 0
    assert results_b[0]["id"] == "n3"
    assert results_b[0]["metadata"]["session_id"] == session_b
    
    # Verify metadata preservation
    node_data = store.get_node("n1", session_a)
    assert node_data is not None
    assert node_data["metadata"]["source_file"] == "doc.pdf"
    assert node_data["metadata"]["modality"] == "pdf_text"
    
    store.delete_session(session_a)
    
    results_a_after = store.query_text("What is the capital of France?", session_a)
    assert len(results_a_after) == 0
    
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir, ignore_errors=True)
