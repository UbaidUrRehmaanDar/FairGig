import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from detector import detect_anomalies

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")


def _parse_origin_list(raw: str) -> List[str]:
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


def _parse_allowed_origins(raw: str, fallback: List[str]) -> List[str]:
    merged = {origin.strip().rstrip("/") for origin in fallback if origin.strip()}
    merged.update(_parse_origin_list(raw))
    return sorted(merged)


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3005",
    "http://localhost:3006",
    "http://localhost:3007",
    "http://localhost:3015",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3005",
    "http://127.0.0.1:3006",
    "http://127.0.0.1:3007",
    "http://127.0.0.1:3015",
]
DEFAULT_ALLOWED_ORIGINS.extend(_parse_origin_list(os.getenv("FRONTEND_URL", "")))
DEFAULT_ALLOWED_ORIGINS.extend(_parse_origin_list(os.getenv("VERCEL_FRONTEND_URL", "")))
ALLOWED_ORIGINS = _parse_allowed_origins(
    os.getenv("ANOMALY_ALLOWED_ORIGINS", ""),
    DEFAULT_ALLOWED_ORIGINS,
)

app = FastAPI(title="FairGig Anomaly Detection Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


def _to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _build_detect_response(req: DetectRequest) -> Dict[str, Any]:
    earnings_payload = [_to_dict(record) for record in req.earnings]
    anomalies = detect_anomalies(earnings_payload)
    return {
        "worker_id": req.worker_id,
        "records_analyzed": len(req.earnings),
        "anomalies_found": len(anomalies),
        "anomalies": anomalies,
    }


@app.post("/anomaly/detect")
async def detect(req: DetectRequest):
    return _build_detect_response(req)


@app.post("/detect")
async def detect_legacy(req: DetectRequest):
    return _build_detect_response(req)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fairgig-anomaly"}
