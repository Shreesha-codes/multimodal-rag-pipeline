from typing import List
from backend.models import MultimodalNode
from backend.services.graph import SessionGraph

def link_temporal(graph: SessionGraph, nodes: List[MultimodalNode], tolerance: float = 2.0):
    audio_nodes = [n for n in nodes if n.modality == "audio"]
    frame_nodes = [n for n in nodes if n.modality == "video_frame"]
    
    for audio in audio_nodes:
        if audio.timestamp is None or audio.end_timestamp is None:
            continue
            
        start_time = audio.timestamp - tolerance
        end_time = audio.end_timestamp + tolerance
        
        for frame in frame_nodes:
            if frame.timestamp is not None and start_time <= frame.timestamp <= end_time:
                graph.add_relationship(
                    source_id=audio.id,
                    target_id=frame.id,
                    rel_type="VISIBLE_DURING"
                )

def link_entities(graph: SessionGraph, nodes: List[MultimodalNode]):
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node_a = nodes[i]
            node_b = nodes[j]
            
            entities_a = node_a.entities or []
            entities_b = node_b.entities or []
            
            # Filter out short or generic entities
            valid_a = {e.lower().strip() for e in entities_a if len(e.strip()) > 2}
            valid_b = {e.lower().strip() for e in entities_b if len(e.strip()) > 2}
            
            intersection = valid_a.intersection(valid_b)
            if intersection:
                graph.add_relationship(
                    source_id=node_a.id,
                    target_id=node_b.id,
                    rel_type="RELATED_TO",
                    shared_entities=list(intersection)
                )
