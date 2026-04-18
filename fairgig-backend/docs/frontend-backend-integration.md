# FairGig Frontend-Backend Integration Guide

This document is for frontend developers integrating with the currently implemented backend.
It covers all implemented backend phases, service setup, authentication, endpoint contracts, role requirements, and integration notes.

## 1) Services and Base URLs

FairGig backend runs as two services:

- Core API: `http://localhost:8000`
- Anomaly API: `http://localhost:8001`

Frontend runtime config currently expects:

- `apiBase` -> Core API
- `anomalyBase` -> Anomaly API

## 2) Required Frontend Environment/Config

For Nuxt runtime public config, keep:

```ts
runtimeConfig: {
  public: {
    apiBase: "http://localhost:8000",
    anomalyBase: "http://localhost:8001",
  },
}
```

The frontend should also be configured with Supabase client values:

- `SUPABASE_URL`
- `SUPABASE_KEY` or `SUPABASE_ANON_KEY`

## 3) Authentication Contract

### JWT Source

- User signs in via Supabase Auth.
- Frontend reads `session.access_token`.
- Send token as `Authorization: Bearer <token>` to all protected Core API routes.

### Role Enforcement

Role is read from JWT metadata (`user_metadata.role` then `app_metadata.role`).

- `worker`: can log shifts, upload screenshot, create grievance, request certificate
- `verifier`: can review screenshots and see pending queue
- `advocate`: can review screenshots, escalate grievances, view analytics

### Common Auth Errors

- `401 Missing bearer token`
- `401 Token invalid or expired`
- `403 Insufficient role`

## 4) Phase-by-Phase Integration

## Phase 1 - Foundation

### 4.1 Core Health Check

- Method: `GET`
- URL: `/health`
- Auth: No
- Response:

```json
{
  "status": "ok",
  "service": "fairgig-core"
}
```

### 4.2 Setup Worker/Verifier/Advocate Profile

- Method: `POST`
- URL: `/auth/setup-profile`
- Auth: Yes (any authenticated user)
- Body:

```json
{
  "full_name": "Rehan Abrar",
  "city_zone": "Gulberg",
  "platform_category": "ride_hailing",
  "role": "worker"
}
```

Important backend behavior:

- Request `role` is ignored for security.
- Backend trusts role from JWT token metadata.

Success response:

```json
{
  "id": "<uuid>",
  "role": "worker",
  "status": "profile_saved"
}
```

## Phase 2 - Shifts and Screenshots

### 4.3 Log Shift

- Method: `POST`
- URL: `/shifts`
- Auth: `worker`
- Body:

```json
{
  "platform": "Careem",
  "shift_date": "2026-04-18",
  "hours_worked": 8,
  "gross_earned": 5000,
  "platform_deductions": 900,
  "net_received": 4100,
  "notes": "Peak hour shift"
}
```

Success response:

```json
{
  "shift_id": "<uuid>",
  "status": "logged",
  "worker_id": "<uuid>",
  "payload": {
    "platform": "Careem",
    "shift_date": "2026-04-18",
    "hours_worked": 8,
    "gross_earned": 5000,
    "platform_deductions": 900,
    "net_received": 4100,
    "notes": "Peak hour shift"
  }
}
```

### 4.4 List Worker Shifts

- Method: `GET`
- URL: `/shifts`
- Auth: `worker`
- Response: array of worker's own shifts (latest first)

### 4.5 Shift Summary

- Method: `GET`
- URL: `/shifts/summary`
- Auth: `worker`
- Response:

```json
{
  "this_month": 12345,
  "this_week": 3456,
  "avg_hourly": 550,
  "avg_commission_pct": 18.3,
  "total_shifts": 12
}
```

### 4.6 City Median

- Method: `GET`
- URL: `/shifts/city-median?platform=<platform-name>`
- Auth: `worker`

Success response when data exists:

```json
{
  "platform": "Careem",
  "city_zone": "Gulberg",
  "platform_category": "ride_hailing",
  "median_hourly": 620,
  "median_daily": 4300,
  "avg_commission_pct": 21.4,
  "sample_size": 75
}
```

Fallback response when no current-month median exists:

```json
{
  "platform": "Careem",
  "city_zone": "Gulberg",
  "platform_category": "ride_hailing",
  "median_hourly": null,
  "median_daily": null,
  "avg_commission_pct": null,
  "sample_size": 0,
  "note": "No current-month city median found for this platform and zone."
}
```

### 4.7 Upload Screenshot for a Shift

- Method: `POST`
- URL: `/screenshots/upload/{shift_id}`
- Auth: `worker`
- Content-Type: `multipart/form-data`
- Form field: `file`

Success response:

```json
{
  "status": "uploaded",
  "screenshot_id": "<uuid>",
  "shift_id": "<uuid>",
  "storage_path": "screenshots/...",
  "review_status": "pending",
  "created_at": "2026-04-18T12:00:00+00:00",
  "filename": "proof.png",
  "worker_id": "<uuid>"
}
```

### 4.8 Pending Screenshot Queue

- Method: `GET`
- URL: `/screenshots/pending`
- Auth: `verifier` or `advocate`
- Response: array of pending screenshot review rows

### 4.9 Review Screenshot

- Method: `PATCH`
- URL: `/screenshots/{screenshot_id}/review`
- Auth: `verifier` or `advocate`
- Body:

```json
{
  "status": "verified",
  "note": "Clear screenshot"
}
```

Allowed status values:

- `verified`
- `flagged`
- `unverifiable`

This also updates parent shift status mapping:

- `verified` -> shift `verified`
- `flagged` -> shift `disputed`
- `unverifiable` -> shift `unverified`

### 4.10 View Private Screenshot

- Method: `GET`
- URL: `/screenshots/view/{screenshot_id}`
- Auth: Yes
- Access rule:
  - worker can view own screenshot only
  - verifier/advocate can view any screenshot

Query option:

- `?redirect=true` (default): 307 redirect to signed URL
- `?redirect=false`: returns signed URL JSON

JSON response when `redirect=false`:

```json
{
  "screenshot_id": "<uuid>",
  "worker_id": "<uuid>",
  "bucket": "earnings",
  "storage_path": "screenshots/...",
  "signed_url": "https://...",
  "expires_in": 60
}
```

## Phase 3 - Grievances and Analytics

### 4.11 Create Grievance

- Method: `POST`
- URL: `/grievances`
- Auth: `worker`
- Body:

```json
{
  "platform": "Careem",
  "category": "commission_change",
  "title": "Commission increased",
  "description": "Commission jumped this week",
  "tags": ["commission", "urgent"]
}
```

### 4.12 List Grievances with Filters

- Method: `GET`
- URL: `/grievances?platform=&category=&status=`
- Auth: No
- Response shape:

```json
{
  "items": [],
  "count": 0,
  "filters": {
    "platform": null,
    "category": null,
    "status": null
  }
}
```

### 4.13 Upvote Grievance

- Method: `POST`
- URL: `/grievances/{grievance_id}/upvote`
- Auth: Yes
- Response:

```json
{
  "ok": true,
  "grievance_id": "<uuid>",
  "upvotes": 7,
  "user_id": "<uuid>",
  "updated_at": "2026-04-18T12:00:00+00:00"
}
```

### 4.14 Escalate Grievance

- Method: `PATCH`
- URL: `/grievances/{grievance_id}/escalate`
- Auth: `advocate`
- Response:

```json
{
  "status": "escalated",
  "grievance_id": "<uuid>",
  "escalated_by": "<uuid>",
  "updated_at": "2026-04-18T12:00:00+00:00"
}
```

### 4.15 Advocate KPIs

- Method: `GET`
- URL: `/analytics/kpis`
- Auth: `advocate`
- Response object contains four arrays:

- `commission_trends`
- `income_by_zone`
- `vulnerability_flags`
- `top_complaints`

## Phase 4 - Anomaly Service

This service is separate from Core API.

### 4.16 Anomaly Health

- Method: `GET`
- URL: `http://localhost:8001/health`
- Auth: No

### 4.17 Detect Anomalies (Primary)

- Method: `POST`
- URL: `http://localhost:8001/anomaly/detect`
- Auth: No
- Body:

```json
{
  "worker_id": "test-001",
  "earnings": [
    {
      "date": "2026-03-01",
      "platform": "Careem",
      "gross_earned": 5000,
      "platform_deductions": 1000,
      "net_received": 4000,
      "hours_worked": 8
    }
  ]
}
```

Response:

```json
{
  "worker_id": "test-001",
  "records_analyzed": 3,
  "anomalies_found": 2,
  "anomalies": [
    {
      "date": "2026-03-02",
      "platform": "Careem",
      "type": "unusual_deduction",
      "severity": "critical",
      "value": 30.0,
      "explanation": "..."
    }
  ]
}
```

Implemented anomaly types:

- `unusual_deduction` (Z-score based, threshold > 2.0)
- `income_drop` (>20% drop vs previous shift)
- `zero_net` (gross > 0 and net <= 0)

### 4.18 Detect Anomalies (Legacy Compatibility)

- Method: `POST`
- URL: `http://localhost:8001/detect`
- Auth: No
- Behavior: same as `/anomaly/detect`

## Phase 5 - Certificate and Seed Data

### 4.19 Certificate Data

- Method: `GET`
- URL: `/certificates/data?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- Auth: `worker`
- Rule: only returns verified shifts in date range

Success response:

```json
{
  "worker": {
    "id": "<uuid>",
    "full_name": "Rehan Abrar",
    "city_zone": "Gulberg",
    "platform_category": "ride_hailing",
    "role": "worker"
  },
  "period": {
    "start": "2026-04-01",
    "end": "2026-04-18"
  },
  "shifts": [],
  "summary": {
    "total_gross": 10000,
    "total_net": 7600,
    "total_shifts": 3,
    "total_hours": 20,
    "avg_commission_pct": 24
  }
}
```

### 4.20 Seed Script (Demo Data)

Script path: `fairgig-backend/core/seed.py`

What it does:

- Inserts or updates demo worker profiles
- Inserts at least 50 verified shifts (`SEED_SHIFT_COUNT`, minimum forced to 50)
- Refreshes materialized view `city_medians`
- Prints verification counts and sample row from `city_medians`

Run command:

```bash
cd fairgig-backend/core
python seed.py
```

## 5) Complete Endpoint Catalog

All currently implemented backend endpoints:

| Service | Method | Path | Auth | Role |
|---|---|---|---|---|
| Core | GET | `/health` | No | Public |
| Core | POST | `/auth/setup-profile` | Yes | Any authenticated |
| Core | POST | `/shifts` | Yes | worker |
| Core | GET | `/shifts` | Yes | worker |
| Core | GET | `/shifts/summary` | Yes | worker |
| Core | GET | `/shifts/city-median?platform=` | Yes | worker |
| Core | POST | `/screenshots/upload/{shift_id}` | Yes | worker |
| Core | GET | `/screenshots/pending` | Yes | verifier/advocate |
| Core | PATCH | `/screenshots/{screenshot_id}/review` | Yes | verifier/advocate |
| Core | GET | `/screenshots/view/{screenshot_id}` | Yes | owner or verifier/advocate |
| Core | POST | `/grievances` | Yes | worker |
| Core | GET | `/grievances` | No | Public |
| Core | POST | `/grievances/{grievance_id}/upvote` | Yes | Any authenticated |
| Core | PATCH | `/grievances/{grievance_id}/escalate` | Yes | advocate |
| Core | GET | `/analytics/kpis` | Yes | advocate |
| Core | GET | `/certificates/data?start_date=&end_date=` | Yes | worker |
| Anomaly | GET | `/health` | No | Public |
| Anomaly | POST | `/anomaly/detect` | No | Public |
| Anomaly | POST | `/detect` | No | Public |

## 6) Frontend Integration Checklist

- Initialize Supabase session flow first (login/confirm).
- Wrap all protected Core calls with `Authorization: Bearer <access_token>`.
- Build role-aware UI routes:
  - worker: shifts, certificate, grievance create
  - verifier: screenshot pending + review
  - advocate: screenshot review + escalation + analytics
- Use `multipart/form-data` only for screenshot upload endpoint.
- Use `anomalyBase` for anomaly calls, not `apiBase`.
- For certificate page:
  - always pass both `start_date` and `end_date`
  - handle empty `shifts` array gracefully
- For city median panel:
  - handle null medians and show the backend `note` message.

## 7) Known Backend Notes Relevant to Frontend

- `POST /grievances` and `POST /shifts` return clear `400` detail if worker profile is missing.
- Screenshot view signed URLs expire quickly (`expires_in = 60`), so frontend should open immediately.
- Anomaly endpoint is public by design for judge testing; no bearer token required.

## 8) Quick Postman Smoke Set (Recommended)

Run these in order:

1. `GET /health` (core)
2. `POST /auth/setup-profile`
3. `POST /shifts`
4. `GET /shifts`
5. `POST /screenshots/upload/{shift_id}`
6. `GET /screenshots/pending` (verifier token)
7. `PATCH /screenshots/{id}/review`
8. `GET /certificates/data?start_date=&end_date=`
9. `GET /analytics/kpis` (advocate token)
10. `POST http://localhost:8001/anomaly/detect`

This verifies full frontend-connectable backend flow across all implemented phases.
