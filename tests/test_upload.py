import pytest
import os
import shutil
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    os.makedirs("storage/uploads", exist_ok=True)
    yield
    if os.path.exists("storage/uploads"):
        shutil.rmtree("storage/uploads")

def test_single_upload():
    file_content = b"test content"
    response = client.post(
        "/upload",
        files=[("files", ("test1.txt", file_content, "text/plain"))]
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["files"]) == 1
    assert data["files"][0]["original_filename"] == "test1.txt"
    assert data["files"][0]["processing_status"] == "uploaded"

def test_multiple_uploads():
    response = client.post(
        "/upload",
        files=[
            ("files", ("test1.txt", b"content1", "text/plain")),
            ("files", ("test2.pdf", b"content2", "application/pdf"))
        ]
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["files"]) == 2

def test_unsupported_extension():
    response = client.post(
        "/upload",
        files=[("files", ("test.exe", b"bad", "application/x-msdownload"))]
    )
    assert response.status_code == 400
    assert "Unsupported format" in response.json()["detail"]

def test_empty_file():
    response = client.post(
        "/upload",
        files=[("files", ("test.txt", b"", "text/plain"))]
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_duplicate_name(tmp_path):
    response = client.post(
        "/upload",
        files=[
            ("files", ("test.txt", b"1", "text/plain")),
            ("files", ("test.txt", b"2", "text/plain"))
        ]
    )
    assert response.status_code == 400
    assert "Duplicate file name" in response.json()["detail"]

def test_status_endpoint():
    upload_response = client.post(
        "/upload",
        files=[("files", ("status_test.txt", b"content", "text/plain"))]
    )
    session_id = upload_response.json()["session_id"]
    
    status_response = client.get(f"/status/{session_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["session_id"] == session_id
    assert status_data["status"] == "active"
    assert len(status_data["files"]) == 1
    assert status_data["files"][0]["original_filename"] == "status_test.txt"

def test_status_not_found():
    response = client.get("/status/session_invalid")
    assert response.status_code == 404
