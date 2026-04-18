import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from detector import detect_anomalies

load_dotenv()


def _parse_allowed_origins(raw: str, fallback: List[str]) -> List[str]:
    if not raw:
        return fallback
    parsed = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return parsed or fallback


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-nuxt-app.vercel.app",
]
ALLOWED_ORIGINS = _parse_allowed_origins(
    os.getenv("ANOMALY_ALLOWED_ORIGINS", ""),
    DEFAULT_ALLOWED_ORIGINS,
)

app = FastAPI(title="FairGig Anomaly Detection Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)


class EarningsRecord(BaseModel):
    date: str
    platform: str
    gross_earned: float
    platform_deductions: float
    net_received: float
    hours_worked: Optional[float] = None


class DetectRequest(BaseModel):
    worker_id: str
    earnings: List[EarningsRecord]


@app.post("/detect")
async def detect(req: DetectRequest):
    anomalies = detect_anomalies([record.dict() for record in req.earnings])
    return {
        "worker_id": req.worker_id,
        "records_analyzed": len(req.earnings),
        "anomalies_found": len(anomalies),
        "anomalies": anomalies,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fairgig-anomaly"}
