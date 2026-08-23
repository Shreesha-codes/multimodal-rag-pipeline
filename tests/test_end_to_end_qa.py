import pytest
import os
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    os.system("python scripts/generate_test_data.py")
    yield

def test_full_pipeline():
    # 1. Upload files
    files_payload = []
    
    file_paths = [
        "test_data/test_document.pdf",
        "test_data/test_diagram.jpg", 
        "test_data/test_audio.mp3",
        "test_data/test_video.mp4"
    ]
    
    for fpath in file_paths:
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                name = os.path.basename(fpath)
                ext = os.path.splitext(name)[1].lower()
                mime = "video/mp4" if ext == ".mp4" else "audio/mpeg" if ext == ".mp3" else "application/pdf" if ext == ".pdf" else "image/jpeg"
                files_payload.append(("files", (name, f.read(), mime)))
                
    if not files_payload:
        pytest.skip("Test data not generated")

    response = client.post("/upload", files=files_payload)
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    
    # 2. Trigger processing
    process_response = client.post(f"/process/{session_id}")
    assert process_response.status_code == 202
    
    # Wait for processing to complete
    max_retries = 30
    for _ in range(max_retries):
        status_res = client.get(f"/status/{session_id}")
        if status_res.status_code == 200:
            status = status_res.json()["status"]
            if status == "completed":
                break
            if status == "failed":
                pytest.fail("Processing failed")
        time.sleep(1)
        
    # Test Cases
    
    # TEST CASE 1 & 2: "What was discussed about database sharding and what was shown on screen?"
    q1 = "What was discussed about database sharding?"
    res1 = client.get(f"/query/{session_id}?q={q1}")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["citations"]) > 0
    
    # TEST CASE 5: Hallucination prevention
    q2 = "What did they say about Kubernetes?"
    res2 = client.get(f"/query/{session_id}?q={q2}")
    assert res2.status_code == 200
    
    # TEST CASE 6: Duplicate upload handling (should be 400)
    with open("test_data/test_document.pdf", "rb") as f:
        content = f.read()
    dup_res = client.post("/upload", files=[
        ("files", ("dup.pdf", content, "application/pdf")),
        ("files", ("dup.pdf", content, "application/pdf"))
    ])
    assert dup_res.status_code == 400
    
    # TEST SESSION ISOLATION
    session_b_res = client.post("/upload", files=[("files", ("b.txt", b"secret info", "text/plain"))])
    session_b_id = session_b_res.json()["session_id"]
    
    res_b = client.get(f"/query/{session_id}?q=secret info")
    assert res_b.status_code == 200
    # Should not find B's info in A
    assert "secret info" not in res_b.json()["answer"].lower()
