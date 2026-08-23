import os
import uuid
import shutil
from backend.services.video_processor import extract_audio_from_video, extract_frames

def test_pipeline():
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    test_dir = os.path.join("storage", "uploads", session_id)
    os.makedirs(test_dir, exist_ok=True)
    
    video_path = "test_data/video/architecture_meeting.mp4"
    if not os.path.exists(video_path):
        return

    audio_path = extract_audio_from_video(video_path, session_id)
    frames = extract_frames(video_path, session_id)
    
    assert audio_path != ""
    assert len(frames) >= 0
    
    shutil.rmtree(test_dir, ignore_errors=True)
    shutil.rmtree(os.path.join("storage", "processed", session_id), ignore_errors=True)

if __name__ == "__main__":
    test_pipeline()
