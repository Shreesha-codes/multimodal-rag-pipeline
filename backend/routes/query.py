from fastapi import APIRouter, Query, HTTPException
from backend.services.vector_store import VectorStore
from backend.services.retrieval_engine import RetrievalEngine

router = APIRouter(prefix="", tags=["Query"])
vector_store = VectorStore()

@router.get("/query/{session_id}")
def query_session(session_id: str, q: str = Query(..., min_length=1), top_k: int = 5):
    try:
        engine = RetrievalEngine(session_id, vector_store)
        bundle = engine.retrieve(q, top_k)
        return bundle
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
