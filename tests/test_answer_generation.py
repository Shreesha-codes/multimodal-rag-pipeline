import pytest
from backend.models import EvidenceBundle, EvidenceItem
from backend.services.answer_generator import generate_answer

def test_citation_validation(monkeypatch):
    # Mock settings to have an API key so we bypass the missing key check
    monkeypatch.setattr("backend.config.settings.google_api_key", "mock_key")
    
    # Mock genai generative model to return a controlled JSON response
    class MockResponse:
        text = '''
        {
            "answer": "Database sharding splits data.",
            "cited_node_ids": ["valid_node_1", "hallucinated_node_999"],
            "confidence": "high"
        }
        '''
        
    class MockModel:
        def generate_content(self, prompt):
            return MockResponse()
            
    monkeypatch.setattr("google.generativeai.GenerativeModel", lambda *args, **kwargs: MockModel())
    monkeypatch.setattr("google.generativeai.configure", lambda *args, **kwargs: None)
    
    bundle = EvidenceBundle(
        query="What is sharding?",
        session_id="test_session",
        evidence=[
            EvidenceItem(
                node_id="valid_node_1",
                modality="audio",
                score=0.9,
                source_file="talk.mp4",
                timestamp=10.5
            )
        ]
    )
    
    final_response = generate_answer("What is sharding?", bundle)
    
    assert final_response.answer == "Database sharding splits data."
    
    # The hallucinated_node_999 MUST be stripped out because it's not in evidence_map
    assert len(final_response.citations) == 1
    
    # The citation metadata MUST be derived from the EvidenceBundle, not the LLM
    citation = final_response.citations[0]
    assert citation["node_id"] == "valid_node_1"
    assert citation["modality"] == "audio"
    assert citation["source"] == "talk.mp4"
    assert citation["timestamp"] == 10.5

def test_empty_evidence():
    bundle = EvidenceBundle(query="test", session_id="session", evidence=[])
    final_response = generate_answer("test", bundle)
    assert final_response.answer == "No relevant evidence found in this session."
    assert len(final_response.citations) == 0
