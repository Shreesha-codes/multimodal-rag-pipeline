import os
import uuid
import shutil
import mimetypes
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="", tags=["Upload"])

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mov", ".mp3", ".wav",
    ".png", ".jpg", ".jpeg", ".pdf", ".txt"
}

MAX_FILE_SIZE = 1024 * 1024 * 500

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    session_dir = os.path.join("storage", "uploads", session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    saved_files = []
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    for file in files:
        if not file.filename:
            continue
            
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")
            
        file_path = os.path.join(session_dir, file.filename)
        
        if os.path.exists(file_path):
            raise HTTPException(status_code=400, detail=f"Duplicate file name: {file.filename}")
            
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        if size == 0:
            raise HTTPException(status_code=400, detail=f"Empty file: {file.filename}")
            
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large: {file.filename}")
            
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception:
            raise HTTPException(status_code=500, detail=f"Failed to save {file.filename}")
            
        mime_type, _ = mimetypes.guess_type(file.filename)
        
        saved_files.append({
            "session_id": session_id,
            "file_id": uuid.uuid4().hex,
            "original_filename": file.filename,
            "mime_type": mime_type,
            "extension": ext,
            "file_size": size,
            "storage_path": file_path,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "processing_status": "uploaded"
        })
        
    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid files provided")
        
    return {"session_id": session_id, "files": saved_files}

@router.get("/status/{session_id}")
async def get_status(session_id: str):
    session_dir = os.path.join("storage", "uploads", session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")
        
    files_info = []
    for filename in os.listdir(session_dir):
        file_path = os.path.join(session_dir, filename)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            ext = os.path.splitext(filename)[1].lower()
            mime_type, _ = mimetypes.guess_type(filename)
            
            files_info.append({
                "session_id": session_id,
                "original_filename": filename,
                "mime_type": mime_type,
                "extension": ext,
                "file_size": size,
                "storage_path": file_path,
                "processing_status": "uploaded"
            })
            
    return {"session_id": session_id, "status": "active", "files": files_info}

@router.get("/files/{session_id}")
async def get_files(session_id: str):
    return await get_status(session_id)
