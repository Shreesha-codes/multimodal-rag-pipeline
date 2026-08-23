import json
from google import genai
from typing import List, Dict, Any
from backend.models import EvidenceBundle, FinalResponse
from backend.config import settings

def generate_answer(query: str, bundle: EvidenceBundle) -> FinalResponse:
    if not bundle.evidence:
        return FinalResponse(
            answer="No relevant evidence found in this session.",
            citations=[],
            confidence="high",
            evidence_bundle=bundle
        )
        
    if not settings.google_api_key:
        return FinalResponse(
            answer="Google API key not configured. Cannot generate text response.",
            citations=[],
            confidence="none",
            evidence_bundle=bundle
        )
        
    context_parts = []
    evidence_map = {}
    
    for item in bundle.evidence:
        evidence_map[item.node_id] = item
        text = item.text_content or "[No text available, visual or structural node]"
        
        context_parts.append(f"--- EVIDENCE ITEM ---\nNODE_ID: {item.node_id}\nMODALITY: {item.modality}\nTEXT/CONTENT: {text}\n")
        
    context_str = "\n".join(context_parts)
    
    prompt = f"""
    You are an expert multimodal analyst. Answer the user's query based ONLY on the provided evidence.
    
    RULES:
    1. Answer ONLY from supplied evidence. Never invent facts.
    2. State when evidence is insufficient.
    3. Return the exact NODE_ID for any evidence you use to form your answer.
    4. Distinguish evidence from inference.
    5. Do NOT generate your own timestamps, page numbers, or filenames. Only output the NODE_IDs.
    
    USER QUERY: {query}
    
    EVIDENCE:
    {context_str}
    
    RETURN STRICT JSON:
    {{
        "answer": "Your detailed answer here...",
        "cited_node_ids": ["node_id_1", "node_id_2"],
        "confidence": "high/medium/low/insufficient evidence"
    }}
    """
    
    try:
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt
        )
        
        if not response or not response.text:
            raise ValueError("Empty response from model")
            
        json_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_text)
        
        answer_text = data.get("answer", "")
        cited_ids = data.get("cited_node_ids", [])
        confidence = data.get("confidence", "unknown")
        
        final_citations = []
        for cid in cited_ids:
            if cid in evidence_map:
                ev = evidence_map[cid]
                citation_data = {
                    "node_id": ev.node_id,
                    "modality": ev.modality,
                    "source": ev.source_file
                }
                if ev.timestamp is not None:
                    citation_data["timestamp"] = ev.timestamp
                if ev.page is not None:
                    citation_data["page"] = ev.page
                final_citations.append(citation_data)
                
        return FinalResponse(
            answer=answer_text,
            citations=final_citations,
            confidence=confidence,
            evidence_bundle=bundle
        )
        
    except Exception as e:
        return FinalResponse(
            answer=f"Error generating answer: {str(e)}",
            citations=[],
            confidence="error",
            evidence_bundle=bundle
        )
