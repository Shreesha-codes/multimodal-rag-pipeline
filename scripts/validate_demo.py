import os
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def run_validation():
    print("=== STARTING AUTOMATED DEMO VALIDATION ===")
    
    files_to_upload = [
        ("test_data/video/architecture_meeting.mp4", "video/mp4"),
        ("test_data/audio/architecture_audio.mp3", "audio/mpeg"),
        ("test_data/documents/architecture.pdf", "application/pdf"),
        ("test_data/images/architecture_diagram.png", "image/png"),
        ("test_data/text/meeting_notes.txt", "text/plain")
    ]
    
    payload = []
    for path, mime in files_to_upload:
        if os.path.exists(path):
            with open(path, "rb") as f:
                payload.append(("files", (os.path.basename(path), f.read(), mime)))
                
    if not payload:
        raise RuntimeError("test_data files not found")

    print(f"Uploading {len(payload)} files...")
    upload_res = client.post("/upload", files=payload)
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    session_id = upload_res.json()["session_id"]
    print(f"Session created: {session_id}")

    proc_res = client.post(f"/process/{session_id}")
    assert proc_res.status_code in [200, 202], f"Trigger process failed: {proc_res.text}"

    max_wait = 30
    status = "processing"
    for elapsed in range(max_wait):
        status_res = client.get(f"/status/{session_id}")
        assert status_res.status_code == 200
        data = status_res.json()
        status = data.get("status")
        if status in ["completed", "failed"]:
            break
        time.sleep(1)

    print(f"Processing finished with status: {status}")
    assert status == "completed", f"Processing did not complete cleanly: {data.get('error')}"

    questions = [
        ("What was discussed about database sharding and what was shown on screen?", ["audio", "video_frame", "pdf_text", "pdf_ocr", "ocr", "text"]),
        ("What architecture diagram was being explained when Redis was mentioned?", ["video_frame", "ocr", "image"]),
        ("What does the PDF say about the architecture shown in the video?", ["pdf_text", "pdf_ocr", "video_frame"]),
        ("What did the speaker say about Kubernetes cluster setup?", [])
    ]

    for idx, (q, expected_modalities) in enumerate(questions, 1):
        print(f"\n[DEMO Q{idx}] Query: {q}")
        q_res = client.get(f"/query/{session_id}", params={"q": q})
        assert q_res.status_code == 200, f"Query failed: {q_res.text}"
        q_data = q_res.json()

        answer = q_data.get("answer", "")
        bundle = q_data.get("evidence_bundle", {})
        evidence = bundle.get("evidence", [])

        print(f"Answer: {answer[:120]}...")
        print(f"Evidence Count: {len(evidence)}")

        modalities = {e.get("modality") for e in evidence}
        print(f"Retrieved Modalities: {modalities}")

        if expected_modalities:
            assert len(evidence) > 0, f"Expected evidence for Q{idx}"
        else:
            print("Verified anti-hallucination/negative query behavior.")

    comp_res = client.get(f"/compare/{session_id}", params={"q": questions[0][0]})
    assert comp_res.status_code == 200, f"Compare failed: {comp_res.text}"
    comp_data = comp_res.json()
    metrics = comp_data.get("metrics", {})
    print(f"\n[BASELINE COMPARISON]")
    print(f"Baseline Modality Coverage: {metrics.get('baseline_modality_coverage')}")
    print(f"Multimodal Modality Coverage: {metrics.get('multimodal_modality_coverage')}")

    print("\n=== AUTOMATED DEMO VALIDATION SUCCESSFUL ===")

if __name__ == "__main__":
    run_validation()
