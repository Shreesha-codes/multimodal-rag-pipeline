from backend.models import EvidenceBundle, EvidenceItem, FinalResponse
from backend.services.vector_store import VectorStore
from backend.services.answer_generator import generate_answer

class BaselineEngine:
    def __init__(self, session_id: str, vector_store: VectorStore):
        self.session_id = session_id
        self.vector_store = vector_store
        
    def retrieve_and_answer(self, query: str, top_k: int = 5) -> FinalResponse:
        nodes = self.vector_store.query_baseline(query, self.session_id, top_k)
        
        evidence_items = []
        for idx, result in enumerate(nodes):
            base_score = 1.0 - (idx * 0.1)
            if base_score < 0.5:
                base_score = 0.5
                
            metadata = result["metadata"]
            
            item = EvidenceItem(
                node_id=result["id"],
                modality=metadata.get("modality", "unknown"),
                score=base_score,
                source_file=metadata.get("source_file", ""),
                text_content=result.get("document"),
                is_primary=True
            )
            evidence_items.append(item)
            
        bundle = EvidenceBundle(
            query=query,
            session_id=self.session_id,
            evidence=evidence_items
        )
        
        return generate_answer(query, bundle)
