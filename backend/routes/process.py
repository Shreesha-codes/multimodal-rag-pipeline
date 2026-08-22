import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.services.ingestion import process_file

router = APIRouter(prefix="", tags=["Process"])

def background_process(session_id: str):
    session_dir = os.path.join("storage", "uploads", session_id)
    if not os.path.exists(session_dir):
        return
        
    for filename in os.listdir(session_dir):
        file_path = os.path.join(session_dir, filename)
        if os.path.isfile(file_path):
            process_file(file_path, session_id)

@router.post("/process/{session_id}")
async def trigger_processing(session_id: str, background_tasks: BackgroundTasks):
    session_dir = os.path.join("storage", "uploads", session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")
        
    background_tasks.add_task(background_process, session_id)
    return {"message": "Processing started in the background", "session_id": session_id}
