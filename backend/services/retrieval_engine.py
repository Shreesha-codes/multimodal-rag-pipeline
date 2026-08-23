from typing import List, Dict, Any, Set
from backend.models import EvidenceItem, EvidenceBundle
from backend.services.vector_store import VectorStore
from backend.services.graph import SessionGraph

class RetrievalEngine:
    def __init__(self, session_id: str, vector_store: VectorStore):
        self.session_id = session_id
        self.vector_store = vector_store
        self.graph = SessionGraph(session_id)
        self.graph.load()
        
    def retrieve(self, query: str, top_k: int = 5) -> EvidenceBundle:
        initial_nodes = self.vector_store.query_text(query, self.session_id, top_k)
        
        evidence_map: Dict[str, EvidenceItem] = {}
        
        for idx, result in enumerate(initial_nodes):
            node_id = result["id"]
            
            # Simple scoring: 1.0 down to 0.5 based on rank/distance
            base_score = 1.0 - (idx * 0.1)
            if base_score < 0.5:
                base_score = 0.5
                
            metadata = result["metadata"]
            
            item = EvidenceItem(
                node_id=node_id,
                modality=metadata.get("modality", "unknown"),
                score=base_score,
                source_file=metadata.get("source_file", ""),
                media_path=metadata.get("media_path"),
                timestamp=metadata.get("timestamp"),
                page=metadata.get("page"),
                text_content=result.get("document"),
                is_primary=True
            )
            evidence_map[node_id] = item
            
        initial_ids = list(evidence_map.keys())
        expanded = self.graph.expand_from_nodes(initial_ids)
        
        for link in expanded:
            target_id = link["node_id"]
            if target_id in evidence_map:
                continue
                
            node_data = link["node_data"]
            rel_data = link["relationship"]
            rel_type = rel_data.get("type", "UNKNOWN")
            
            # Base score for linked nodes
            link_score = 0.7
            if rel_type == "VISIBLE_DURING":
                link_score = 0.9
            elif rel_type == "RELATED_TO":
                link_score = 0.8
                
            item = EvidenceItem(
                node_id=target_id,
                modality=node_data.get("modality", "unknown"),
                score=link_score,
                source_file=node_data.get("source_file", ""),
                media_path=node_data.get("media_path") or node_data.get("source_file"),
                timestamp=node_data.get("timestamp"),
                text_content=node_data.get("text") or node_data.get("ocr_text") or node_data.get("visual_summary"),
                relationship_path=rel_type,
                is_primary=False
            )
            evidence_map[target_id] = item
            
        final_evidence = list(evidence_map.values())
        final_evidence.sort(key=lambda x: x.score, reverse=True)
        
        return EvidenceBundle(
            query=query,
            session_id=self.session_id,
            evidence=final_evidence
        )
