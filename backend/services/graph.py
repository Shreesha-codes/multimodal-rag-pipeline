import os
import networkx as nx
import pickle
from typing import List, Dict, Any
from backend.models import MultimodalNode

class SessionGraph:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.graph = nx.DiGraph()
        
    def add_node(self, node: MultimodalNode):
        self.graph.add_node(
            node.id, 
            modality=node.modality,
            timestamp=node.timestamp,
            end_timestamp=node.end_timestamp,
            source_file=node.source_file,
            text=node.text,
            entities=node.entities,
            ocr_text=node.ocr_text,
            visual_summary=node.visual_summary
        )

    def add_relationship(self, source_id: str, target_id: str, rel_type: str, confidence: float = 1.0, **metadata):
        self.graph.add_edge(source_id, target_id, type=rel_type, confidence=confidence, **metadata)

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        if not self.graph.has_node(node_id):
            return []
            
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.get_edge_data(node_id, neighbor)
            node_data = self.graph.nodes[neighbor]
            neighbors.append({
                "node_id": neighbor,
                "node_data": node_data,
                "relationship": edge_data
            })
        return neighbors

    def expand_from_nodes(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        expanded = []
        for n_id in node_ids:
            expanded.extend(self.get_neighbors(n_id))
        return expanded

    def save(self):
        graph_dir = os.path.join("graph", self.session_id)
        os.makedirs(graph_dir, exist_ok=True)
        file_path = os.path.join(graph_dir, "graph.gpickle")
        with open(file_path, "wb") as f:
            pickle.dump(self.graph, f)

    def load(self):
        file_path = os.path.join("graph", self.session_id, "graph.gpickle")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                self.graph = pickle.load(f)
