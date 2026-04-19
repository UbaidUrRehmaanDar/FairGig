import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

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
    allow_origins=["*"],
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


def _to_str(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_earning_record(raw: Any) -> Dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    date_value = item.get("date") or item.get("shift_date") or item.get("timestamp")
    gross_value = item.get("gross_earned", item.get("gross", item.get("amount", 0)))
    deduction_value = item.get(
        "platform_deductions",
        item.get("deductions", item.get("commission", item.get("platform_take", 0))),
    )
    net_value = item.get(
        "net_received",
        item.get("net", item.get("take_home", item.get("net_earnings", 0))),
    )

    return {
        "date": _to_str(date_value),
        "platform": _to_str(item.get("platform") or item.get("source"), "Unknown platform"),
        "gross_earned": _to_float(gross_value, 0.0),
        "platform_deductions": _to_float(deduction_value, 0.0),
        "net_received": _to_float(net_value, 0.0),
        "hours_worked": _to_optional_float(item.get("hours_worked", item.get("hours"))),
    }


def _extract_detect_payload(payload: Any) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
    warning: Optional[str] = None
    worker_id = "unknown-worker"
    source_rows: List[Any] = []

    if isinstance(payload, list):
        source_rows = payload
        warning = "Received legacy list payload; expected object with worker_id and earnings."
    elif isinstance(payload, dict):
        worker_id = _to_str(
            payload.get("worker_id") or payload.get("workerId") or payload.get("user_id"),
            "unknown-worker",
        )

        if isinstance(payload.get("earnings"), list):
            source_rows = payload.get("earnings")
        elif isinstance(payload.get("shifts"), list):
            source_rows = payload.get("shifts")
            warning = "Received 'shifts' payload; normalized to earnings format."
        elif isinstance(payload.get("data"), list):
            source_rows = payload.get("data")
            warning = "Received 'data' payload; normalized to earnings format."
        elif any(
            key in payload
            for key in (
                "date",
                "shift_date",
                "platform",
                "gross_earned",
                "platform_deductions",
                "net_received",
                "amount",
            )
        ):
            source_rows = [payload]
            warning = "Received single-record payload; wrapped into a one-item earnings list."
    elif payload is not None:
        warning = "Unsupported payload format; expected object or list."

    normalized_rows = [_normalize_earning_record(item) for item in source_rows]
    return worker_id, normalized_rows, warning


def _build_detect_response_from_rows(
    worker_id: str,
    earnings_payload: List[Dict[str, Any]],
    warning: Optional[str] = None,
) -> Dict[str, Any]:
    anomalies = detect_anomalies(earnings_payload)
    response = {
        "worker_id": worker_id,
        "records_analyzed": len(earnings_payload),
        "anomalies_found": len(anomalies),
        "anomalies": anomalies,
    }
    if warning:
        response["warning"] = warning
    return response


def _build_detect_response(req: DetectRequest) -> Dict[str, Any]:
    earnings_payload = [_to_dict(record) for record in req.earnings]
    return _build_detect_response_from_rows(req.worker_id, earnings_payload)


@app.post("/anomaly/detect")
async def detect(payload: Any = Body(default=None)):
    if isinstance(payload, dict):
        try:
            return _build_detect_response(DetectRequest(**payload))
        except ValidationError:
            pass

    worker_id, earnings_payload, warning = _extract_detect_payload(payload)
    return _build_detect_response_from_rows(worker_id, earnings_payload, warning)


@app.post("/detect")
async def detect_legacy(payload: Any = Body(default=None)):
    return await detect(payload)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fairgig-anomaly"}
