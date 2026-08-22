from fastapi import APIRouter, Query, HTTPException
from backend.services.vector_store import VectorStore
from backend.services.retrieval_engine import RetrievalEngine
from backend.services.baseline_engine import BaselineEngine
from backend.services.answer_generator import generate_answer
from backend.models import ComparisonResult, ComparisonMetrics

router = APIRouter(prefix="", tags=["Compare"])
vector_store = VectorStore()

@router.get("/compare/{session_id}")
def compare_session(session_id: str, q: str = Query(..., min_length=1), top_k: int = 5):
    try:
        # 1. Run Baseline
        baseline_engine = BaselineEngine(session_id, vector_store)
        baseline_response = baseline_engine.retrieve_and_answer(q, top_k)
        
        # 2. Run Multimodal (Graph-Expanded)
        retrieval_engine = RetrievalEngine(session_id, vector_store)
        multimodal_bundle = retrieval_engine.retrieve(q, top_k)
        multimodal_response = generate_answer(q, multimodal_bundle)
        
        # 3. Calculate simple coverage metrics
        baseline_modalities = {ev.modality for ev in baseline_response.evidence_bundle.evidence}
        multi_modalities = {ev.modality for ev in multimodal_response.evidence_bundle.evidence}
        
        baseline_sources = {ev.source_file for ev in baseline_response.evidence_bundle.evidence}
        multi_sources = {ev.source_file for ev in multimodal_response.evidence_bundle.evidence}
        
        metrics = ComparisonMetrics(
            baseline_modality_coverage=list(baseline_modalities),
            multimodal_modality_coverage=list(multi_modalities),
            baseline_source_coverage=len(baseline_sources),
            multimodal_source_coverage=len(multi_sources)
        )
        
        return ComparisonResult(
            query=q,
            session_id=session_id,
            baseline=baseline_response,
            multimodal=multimodal_response,
            metrics=metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
