import os
import shutil
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.google_api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

settings = Settings()

def check_system_dependencies() -> dict:
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "tesseract": shutil.which("tesseract") is not None,
        "google_api_key": bool(settings.google_api_key)
    }

def create_required_directories():
    directories = [
        "storage/uploads",
        "storage/processed",
        "storage/sessions",
        "chroma_db",
        "graph"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
