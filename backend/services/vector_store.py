import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from backend.models import MultimodalNode

class VectorStore:
    def __init__(self):
        self.persist_directory = "chroma_db"
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        self.text_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.text_collection = self.client.get_or_create_collection(
            name="text_collection",
            embedding_function=self.text_embedding_fn
        )
        
        self.baseline_collection = self.client.get_or_create_collection(
            name="baseline_collection",
            embedding_function=self.text_embedding_fn
        )
        
    def _assemble_text(self, node: MultimodalNode) -> str:
        parts = []
        if node.text:
            parts.append(node.text)
        if node.ocr_text:
            parts.append(node.ocr_text)
        if node.visual_summary:
            parts.append(node.visual_summary)
            
        return " ".join(parts).strip()
        
    def add_nodes(self, nodes: List[MultimodalNode]):
        ids = []
        documents = []
        metadatas = []
        
        for node in nodes:
            text_content = self._assemble_text(node)
            
            if text_content:
                ids.append(node.id)
                documents.append(text_content)
                
                metadata = {
                    "session_id": node.session_id,
                    "modality": node.modality,
                    "source_file": node.source_file,
                    "timestamp": node.timestamp if node.timestamp is not None else 0.0,
                }
                
                if node.media_path:
                    metadata["media_path"] = node.media_path
                if node.page_number is not None:
                    metadata["page"] = node.page_number
                    
                metadatas.append(metadata)
                
        if ids:
            self.text_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
    def query_text(self, query: str, session_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.text_collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"session_id": session_id}
        )
        
        nodes = []
        if not results["ids"]:
            return nodes
            
        for i in range(len(results["ids"][0])):
            node = {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            }
            nodes.append(node)
            
        return nodes
        
    def query_image(self, image_path: str, session_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return []
        
    def get_node(self, node_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        results = self.text_collection.get(
            ids=[node_id],
            where={"session_id": session_id}
        )
        
        if results and results["ids"]:
            return {
                "id": results["ids"][0],
                "document": results["documents"][0],
                "metadata": results["metadatas"][0]
            }
        return None
        
    def delete_session(self, session_id: str):
        self.text_collection.delete(
            where={"session_id": session_id}
        )
        self.baseline_collection.delete(
            where={"session_id": session_id}
        )
        
    def add_baseline_nodes(self, nodes: List[MultimodalNode]):
        ids = []
        documents = []
        metadatas = []
        
        for node in nodes:
            # For baseline, only use direct text (no OCR, no visual summary if they want pure text, but instructions say "transcript, OCR, PDF text, TXT")
            parts = []
            if node.text:
                parts.append(node.text)
            if node.ocr_text:
                parts.append(node.ocr_text)
                
            text_content = " ".join(parts).strip()
            
            if text_content:
                ids.append(f"baseline_{node.id}")
                documents.append(text_content)
                
                metadata = {
                    "node_id": node.id,
                    "session_id": node.session_id,
                    "modality": node.modality,
                    "source_file": node.source_file,
                }
                metadatas.append(metadata)
                
        if ids:
            self.baseline_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
    def query_baseline(self, query: str, session_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.baseline_collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"session_id": session_id}
        )
        
        nodes = []
        if not results["ids"]:
            return nodes
            
        for i in range(len(results["ids"][0])):
            node = {
                "id": results["metadatas"][0][i]["node_id"],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            }
            nodes.append(node)
            
        return nodes
