import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.services.ingestion import ingest_file

router = APIRouter(prefix="", tags=["Process"])

_session_results: dict = {}

def background_process(session_id: str):
    session_dir = os.path.join("storage", "uploads", session_id)
    if not os.path.exists(session_dir):
        return

    file_results = []
    for filename in os.listdir(session_dir):
        file_path = os.path.join(session_dir, filename)
        if os.path.isfile(file_path):
            result = ingest_file(session_id, file_path)
            file_results.append(result)

    _session_results[session_id] = {
        "session_id": session_id,
        "status": "complete",
        "files": file_results,
        "total_nodes": sum(r["node_count"] for r in file_results),
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
