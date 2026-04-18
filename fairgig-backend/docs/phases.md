# FairGig — Backend Progress Tracker

---

## Phase 1 — Foundation
> Both services running, DB connected, JWT middleware working

- [ ] `.env` file created with all keys (SUPABASE_URL, SERVICE_KEY, JWT_SECRET, DATABASE_URL)
- [ ] `core/` FastAPI app scaffolded — `GET /health` returns 200
- [ ] `anomaly/` FastAPI app scaffolded — `GET /health` returns 200
- [ ] `db.py` asyncpg pool connects to Supabase PostgreSQL
- [ ] `auth_middleware.py` rejects invalid JWT with 401
- [ ] `POST /auth/setup-profile` creates row in `profiles` table
- [ ] CORS configured (localhost:3000 + production URL)

**✅ Gate: Hit `GET /health` on both ports. Send a bad token to any protected route — get 401.**

---

## Phase 2 — Shifts & Screenshots
> Complete worker earnings CRUD + file upload

- [x] `POST /shifts` inserts shift row, returns `shift_id`
- [x] `GET /shifts` returns worker's own shifts (RLS enforced)
- [x] `GET /shifts/summary` returns this_month, this_week, avg_hourly, avg_commission_pct
- [x] `GET /shifts/city-median?platform=` returns median from materialized view
- [x] `POST /screenshots/upload/{shift_id}` uploads file to Supabase Storage
- [x] `GET /screenshots/pending` returns pending queue (verifier/advocate only)
- [x] `PATCH /screenshots/{id}/review` updates screenshot + parent shift status

**✅ Gate: POST a shift via Postman → GET /shifts returns it → upload a screenshot → GET /screenshots/pending shows it.**

---

## Phase 3 — Grievances & Analytics
> Grievance board CRUD + advocate KPI endpoint

- [x] `POST /grievances` creates complaint
- [x] `GET /grievances` returns list, filters by `?platform=&category=&status=`
- [x] `POST /grievances/{id}/upvote` increments upvotes
- [x] `PATCH /grievances/{id}/escalate` sets status to escalated (advocate only)
- [x] `GET /analytics/kpis` returns all four sections:
  - [x] `commission_trends`
  - [x] `income_by_zone`
  - [x] `vulnerability_flags` (workers with >20% income drop)
  - [x] `top_complaints`

**✅ Gate: POST a grievance → GET /grievances returns it with filters working → GET /analytics/kpis returns non-empty data.**

---

## Phase 4 — Anomaly Service
> Separate FastAPI process on port 8001 — judges will call this directly

- [ ] `POST /anomaly/detect` accepts `{ worker_id, earnings[] }` and returns anomalies
- [ ] Unusual deduction detection (Z-score > 2.0) working
- [ ] Income drop detection (>20% shift-on-shift) working
- [ ] Zero-net anomaly detection working
- [ ] Each anomaly has: `date`, `type`, `severity`, `value`, `explanation` (plain English)
- [ ] Tested with judge payload (deduction spike from 20% → 50%)

**✅ Gate: POST judge payload → receive at least 2 anomalies with human-readable explanations.**

```json
{
  "worker_id": "test-001",
  "earnings": [
    {"date": "2026-03-01", "platform": "Careem", "gross_earned": 5000, "platform_deductions": 1000, "net_received": 4000, "hours_worked": 8},
    {"date": "2026-03-02", "platform": "Careem", "gross_earned": 5000, "platform_deductions": 2500, "net_received": 2500, "hours_worked": 8},
    {"date": "2026-03-03", "platform": "Careem", "gross_earned": 5000, "platform_deductions": 1000, "net_received": 1000, "hours_worked": 8}
  ]
}
```

---

## Phase 5 — Certificate & Seed Data
> Printable certificate data endpoint + real data in DB for demo

- [x] `GET /certificates/data?start_date=&end_date=` returns only **verified** shifts in range
- [x] Response includes: worker profile, shifts list, summary totals
- [x] Seed script run — 50+ shifts inserted across platforms/zones
- [x] `REFRESH MATERIALIZED VIEW city_medians` run after seed
- [x] City median endpoint returns non-null values after seed

**✅ Gate: GET /certificates/data with a date range returns verified shifts + totals. City median is non-null.**

---

## Phase 6 — Deployment
> Both services live on public URLs

- [ ] `core` service deployed (Railway / Render / Fly.io)
- [ ] `anomaly` service deployed
- [ ] All env vars set in deployment platform
- [ ] CORS updated with live frontend URL
- [ ] Demo accounts created and tested on production:
  - `worker@fairgig.demo` / `Worker123!`
  - `verifier@fairgig.demo` / `Verifier123!`
  - `advocate@fairgig.demo` / `Advocate123!`
- [ ] API contract table written (markdown or Postman collection)

**✅ Gate: All 3 demo accounts work on live URL. Judge can hit anomaly endpoint via Postman on production.**

---

## Quick Reference

| Service | Local Port | Start Command |
|---|---|---|
| Core API | 8000 | `uvicorn main:app --reload --port 8000` |
| Anomaly API | 8001 | `uvicorn main:app --reload --port 8001` |

| Key | Where to find it |
|---|---|
| `SUPABASE_JWT_SECRET` | Dashboard → Settings → API → JWT Secret |
| `SUPABASE_SERVICE_KEY` | Dashboard → Settings → API → service_role key |
| `DATABASE_URL` | Dashboard → Settings → Database → Connection string |