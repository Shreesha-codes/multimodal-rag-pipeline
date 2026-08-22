import os
import subprocess
import shutil
import uuid
from typing import List, Dict, Tuple
from scenedetect import detect, AdaptiveDetector

def extract_audio_from_video(video_path: str, session_id: str) -> str:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed or not in PATH")
        
    output_dir = os.path.join("storage", "processed", session_id, "audio")
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.wav")
    
    try:
        result = subprocess.run([
            "ffmpeg", "-y", "-i", video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", 
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            if not os.path.exists(output_path):
                return ""
                
        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to extract audio: {str(e)}")

def extract_frames(video_path: str, session_id: str) -> List[Tuple[float, str]]:
    output_dir = os.path.join("storage", "processed", session_id, "frames")
    os.makedirs(output_dir, exist_ok=True)
    
    frames_info = []
    
    try:
        scene_list = detect(video_path, AdaptiveDetector())
        
        if scene_list:
            for i, scene in enumerate(scene_list):
                timestamp = scene[0].get_seconds()
                frame_filename = f"frame_{i}_{timestamp:.2f}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                subprocess.run([
                    "ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
                    "-vframes", "1", "-q:v", "2", frame_path
                ], capture_output=True)
                
                if os.path.exists(frame_path):
                    frames_info.append((timestamp, frame_path))
        else:
            duration = get_video_duration(video_path)
            for i in range(int(duration)):
                timestamp = float(i)
                frame_filename = f"frame_{i}_{timestamp:.2f}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                subprocess.run([
                    "ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
                    "-vframes", "1", "-q:v", "2", frame_path
                ], capture_output=True)
                
                if os.path.exists(frame_path):
                    frames_info.append((timestamp, frame_path))
                    
        return frames_info
    except Exception:
        raise RuntimeError("Failed to extract frames")

def get_video_duration(video_path: str) -> float:
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", video_path
        ], capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0
