import pytest
from backend.models import EvidenceBundle, EvidenceItem
from backend.services.answer_generator import generate_answer

def test_citation_validation(monkeypatch):
    monkeypatch.setattr("backend.config.settings.google_api_key", "mock_key")
    
    class MockResponse:
        text = '''
        {
            "answer": "Database sharding splits data.",
            "cited_node_ids": ["valid_node_1", "hallucinated_node_999"],
            "confidence": "high"
        }
        '''
        
    class MockModels:
        def generate_content(self, model, contents):
            return MockResponse()

    class MockClient:
        def __init__(self, api_key=None):
            self.models = MockModels()
            
    monkeypatch.setattr("google.genai.Client", MockClient)
    
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
    assert len(final_response.citations) == 1
    
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
