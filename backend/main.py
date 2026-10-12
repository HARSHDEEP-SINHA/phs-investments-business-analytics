"""FastAPI application for the synthetic business intelligence project."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .analytics import city_performance, monthly_trend, overview, scheme_performance, sip_summary, transaction_failures
from .agent import answer_question
from .database import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="PHS Business Intelligence API", version="1.0.0",
              description="Demo analytics API backed by synthetic data only.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
                   allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


@app.get("/health")
def health():
    return {"status": "ok", "data": "synthetic"}


@app.get("/api/overview")
def get_overview():
    return overview()


@app.get("/api/monthly")
def get_monthly():
    return {"months": monthly_trend()}


@app.get("/api/cities")
def get_cities(limit: int = 10):
    return {"cities": city_performance(limit)}


@app.get("/api/schemes")
def get_schemes(limit: int = 10):
    return {"schemes": scheme_performance(limit)}


@app.get("/api/sips")
def get_sips():
    return sip_summary()


@app.get("/api/failures")
def get_failures():
    """Aggregate transaction-quality metrics; no transaction-level records are returned."""
    return transaction_failures()


@app.post("/api/chat")
def chat(body: ChatRequest):
    try:
        return answer_question(body.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
