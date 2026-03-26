from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.routes import router


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


app = FastAPI(
    title="AI Chatbot for Forensic Analysis",
    version="0.1.0",
    description="Hackathon-ready forensic analysis assistant for telecom and digital datasets.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
