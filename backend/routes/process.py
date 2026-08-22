import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.services.ingestion import process_file
from backend.services.graph import SessionGraph
from backend.services.relationship_engine import link_temporal, link_entities
from backend.services.vector_store import VectorStore

router = APIRouter(prefix="", tags=["Process"])

_session_results: dict = {}

def background_process(session_id: str):
    session_dir = os.path.join("storage", "uploads", session_id)
    if not os.path.exists(session_dir):
        return
        
    all_nodes = []
    for filename in os.listdir(session_dir):
        file_path = os.path.join(session_dir, filename)
        if os.path.isfile(file_path):
            nodes = process_file(file_path, session_id)
            all_nodes.extend(nodes)
            
    graph = SessionGraph(session_id)
    for node in all_nodes:
        graph.add_node(node)
        
    link_temporal(graph, all_nodes)
    link_entities(graph, all_nodes)
    
    graph.save()
    
    vector_store = VectorStore()
    vector_store.add_nodes(all_nodes)
    vector_store.add_baseline_nodes(all_nodes)

    _session_results[session_id] = {
        "session_id": session_id,
        "status": "complete",
        "total_nodes": len(all_nodes),
    }

@router.post("/process/{session_id}")
async def trigger_processing(session_id: str, background_tasks: BackgroundTasks):
    session_dir = os.path.join("storage", "uploads", session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")

    _session_results[session_id] = {"session_id": session_id, "status": "processing"}
    background_tasks.add_task(background_process, session_id)
    return {"message": "Processing started", "session_id": session_id}

@router.get("/process/results/{session_id}")
async def get_processing_results(session_id: str):
    if session_id not in _session_results:
        raise HTTPException(status_code=404, detail="No results found for this session")
    return _session_results[session_id]
