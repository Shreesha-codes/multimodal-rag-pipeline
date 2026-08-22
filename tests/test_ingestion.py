import os
import urllib.request
import uuid
import shutil
from backend.services.ingestion import process_file

def test_pipeline():
    video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    
    test_dir = os.path.join("storage", "uploads", session_id)
    os.makedirs(test_dir, exist_ok=True)
    video_path = os.path.join(test_dir, "test_video.mp4")
    
    print("Downloading test video...")
    urllib.request.urlretrieve(video_url, video_path)
    
    print(f"Processing video: {video_path}")
    nodes = process_file(video_path, session_id)
    
    video_frames = [n for n in nodes if n.modality == "video_frame"]
    audio_nodes = [n for n in nodes if n.modality == "audio"]
    
    print(f"Extracted {len(video_frames)} frames.")
    print(f"Extracted {len(audio_nodes)} audio segments.")
    
    assert len(video_frames) > 0, "No frames extracted"
    
    audio_dir = os.path.join("storage", "processed", session_id, "audio")
    frames_dir = os.path.join("storage", "processed", session_id, "frames")
    
    assert os.path.exists(audio_dir), "Audio directory not created"
    assert os.path.exists(frames_dir), "Frames directory not created"
    
    print("Pipeline test completed successfully.")
    
    shutil.rmtree(test_dir, ignore_errors=True)
    shutil.rmtree(os.path.join("storage", "processed", session_id), ignore_errors=True)

if __name__ == "__main__":
    test_pipeline()
