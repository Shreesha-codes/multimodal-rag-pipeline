# Multimodal RAG Pipeline

This repository contains a Multimodal Retrieval-Augmented Generation (RAG) Pipeline, featuring a FastAPI backend and a Streamlit frontend. It supports uploading, managing, and eventually processing various media and document formats including videos, audio files, images, and text documents.

## Supported Formats
- **Video**: MP4, MOV
- **Audio**: MP3, WAV
- **Image**: PNG, JPG, JPEG
- **Document**: PDF, TXT

## Prerequisites

Before running the application, you must install the following system dependencies:
1. **Python**: Python 3.9+ is recommended.
2. **FFmpeg**: Required for video and audio processing. Ensure the `ffmpeg` executable is added to your system's `PATH`.
3. **Tesseract OCR**: Required for extracting text from images. Ensure the `tesseract` executable is added to your system's `PATH`.
4. **Google Gemini API Key**: Set your API key in the environment file for generative capabilities.

## Setup Instructions

Follow these steps to set up the project locally.

### 1. Clone the repository
Navigate to your desired folder and clone the repository (or extract the project files).

### 2. Create and Activate a Virtual Environment
It is highly recommended to install the dependencies in an isolated virtual environment (`venv`).

**For Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**For Windows (Command Prompt):**
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

**For macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
With the virtual environment activated, install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

*(Note: Depending on your Python version, some packages that require C++ build tools (like `pydantic-core` or `pandas`) may require Visual Studio Build Tools to be installed on Windows if pre-built binaries are not available).*

### 4. Configure Environment Variables
1. Rename the `.env.example` file to `.env`.
2. Add your required API keys to the `.env` file:
```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

## Running the Application

You need to start both the backend server and the frontend UI. It is recommended to run them in two separate terminal windows with the virtual environment activated in both.

### Start the Backend (FastAPI)
```bash
uvicorn backend.main:app --reload
```
The backend API will be available at `http://localhost:8000`.
You can view the interactive API documentation at `http://localhost:8000/docs`.

### Start the Frontend (Streamlit)
```bash
streamlit run frontend/app.py
```
The frontend UI will automatically open in your default web browser (typically at `http://localhost:8501`).

## Architecture

- **Frontend**: A Streamlit interface for seamless user interaction, batch file uploads, and session tracking.
- **Backend**: A FastAPI REST API handling chunked file streaming, session creation, and metadata generation.
- **Storage**: Media files are stored safely on disk in session-specific directories (`storage/uploads/<session_id>/`) rather than in a database.
