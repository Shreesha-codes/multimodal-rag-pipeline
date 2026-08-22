from fastapi import FastAPI
from backend.routes import health, upload
from backend.config import create_required_directories, check_system_dependencies

app = FastAPI(title="Multimodal RAG API")

app.include_router(health.router)
app.include_router(upload.router)

@app.on_event("startup")
def startup_event():
    create_required_directories()
    deps = check_system_dependencies()
    print(f"System Dependencies Status: {deps}")
    if not deps.get("google_api_key"):
        print("WARNING: GOOGLE_API_KEY is not set. Gemini integration will fail.")
    if not deps.get("ffmpeg"):
        print("WARNING: FFmpeg is not installed. Video/audio processing will fail.")
    if not deps.get("tesseract"):
        print("WARNING: Tesseract is not installed. OCR processing will fail.")
