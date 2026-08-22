from fastapi import FastAPI
from backend.routes import health

app = FastAPI(title="Multimodal RAG API")

app.include_router(health.router)
