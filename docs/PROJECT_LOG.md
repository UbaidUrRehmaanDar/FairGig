# Project Log

## 2026-04-18 - Frontend-Backend Integration Contract Documentation
- Name: Rehan Abrar
- Scope locked to backend only; no files under `fairgig-frontend/` were modified.
- Added comprehensive integration guide for frontend developers at `fairgig-backend/docs/frontend-backend-integration.md`.
- Document includes all currently implemented backend phases and contracts:
  - Service setup and runtime base URLs for Core API and Anomaly API.
  - JWT auth flow, role enforcement rules, and common error responses.
  - Phase-wise endpoint details (Phase 1 through Phase 5) with request/response examples.
  - Full endpoint catalog table with auth and role requirements.
  - Seed script behavior and run instructions for demo data and city median refresh.
  - Frontend integration checklist and known backend notes to reduce integration issues.

## 2026-04-18 - Phase 3 Grievances and Analytics Complete
- Name: Rehan Abrar
- Scope locked to backend only; no files under `fairgig-frontend/` were modified.
- Implemented full grievance board endpoints in `fairgig-backend/core/routers/grievances.py`:
  - `POST /grievances` now inserts complaint rows tied to authenticated worker profile.
  - `GET /grievances` now returns persisted items with filter support for `platform`, `category`, and `status`.
  - `POST /grievances/{id}/upvote` now atomically increments upvotes and updates timestamp.
  - `PATCH /grievances/{id}/escalate` now enforces advocate role and updates grievance status to `escalated`.
- Implemented advocate KPI endpoint in `fairgig-backend/core/routers/analytics.py`:
  - `commission_trends` from shift-level commission percentages.
  - `income_by_zone` from profile city-zone grouped net earnings.
  - `vulnerability_flags` from worker shift-on-shift income drop >20%.
  - `top_complaints` from grievance category counts and upvote totals.
- Updated backend phase tracker in `fairgig-backend/docs/phases.md` by marking all Phase 3 items complete.
- Completed live end-to-end Phase 3 gate verification against running API:
  - Created grievance as worker.
  - Verified listing and filters (`open` and `escalated`) include created grievance.
  - Verified upvote increment endpoint.
  - Verified escalate action via advocate role.
  - Verified `/analytics/kpis` returns all four non-empty KPI sections.

## 2026-04-18 - Phase 4 Anomaly Service Verification (Code Review)
- Name: GitHub Copilot
- Verified Phase 4 contract is implemented in `fairgig-backend/anomaly/`:
  - `POST /anomaly/detect` accepts `{ worker_id, earnings[] }` and returns `anomalies[]`.
  - Detector covers `unusual_deduction` (Z-score > 2.0), `income_drop` (>20%), and `zero_net` anomalies.
  - Each anomaly includes `date`, `platform`, `type`, `severity`, `value`, and a plain-English `explanation`.
- Updated the Phase 4 checklist in `fairgig-backend/docs/phases.md` accordingly.
- Note: `fairgig-backend/core/routers/shifts.py` currently posts to `${ANOMALY_SERVICE_URL}/detect/single`, but the anomaly service exposes `/detect` and `/anomaly/detect` (no `/detect/single`). If you want shift logging to ping the sidecar, align these paths.

## 2026-04-18 - Screenshots Router Post-Pull Startup Fix
- Name: Rehan Abrar
- Scope locked to backend only; no files under `fairgig-frontend/` were modified.
- Fixed post-pull startup regression in `fairgig-backend/core/routers/screenshots.py`:
  - Added missing imports used by `GET /screenshots/view/{screenshot_id}` (`get_current_user`, `UUID`, `RedirectResponse`).
  - Restored signed URL helper utilities used by the view endpoint (`_extract_signed_url`, `_to_absolute_signed_url`).
  - Added bucket resolver helper (`_get_bucket_name`) and reused it in upload + view paths.
  - Replaced broken helper call chain with active client usage (`get_supabase_client().storage.from_(bucket).create_signed_url(...)`).
- Result: core API import path no longer crashes on `NameError` during startup.

## 2026-04-18 - Private Screenshot View Proxy Endpoint
- Name: Rehan Abrar
- Scope locked to backend only; no files under `fairgig-frontend/` were modified.
- Added secure screenshot viewing endpoint in `fairgig-backend/core/routers/screenshots.py`:
  - Implemented `GET /screenshots/view/{screenshot_id}` for authenticated access to private bucket files.
  - Added role/ownership enforcement: workers can view only their own screenshots, while verifier/advocate can view any screenshot.
  - Endpoint now generates a 60-second signed Supabase Storage URL for private bucket access.
  - Default behavior redirects (`307`) to the signed URL for direct image rendering.
  - Added `?redirect=false` option to return JSON payload with signed URL metadata for frontend-controlled navigation.

## 2026-04-18 - Phase 2 Backend Shifts and Screenshots Complete
- Name: Rehan Abrar
- Scope locked to backend only; no files under `fairgig-frontend/` were modified.
- Implemented full Phase 2 shift endpoints in `fairgig-backend/core/routers/shifts.py`:
  - `POST /shifts` now inserts into `shifts` and returns persisted shift payload with `shift_id`.
  - `GET /shifts` now returns only the authenticated worker's shifts.
  - `GET /shifts/summary` now calculates `this_month`, `this_week`, `avg_hourly`, and `avg_commission_pct` from DB.
  - `GET /shifts/city-median` now reads from `city_medians` when present and uses a computed fallback when the view is missing.
- Implemented full Phase 2 screenshot workflow in `fairgig-backend/core/routers/screenshots.py`:
  - `POST /screenshots/upload/{shift_id}` now validates ownership, uploads to Supabase Storage bucket, creates `earnings_screenshots` row, and marks parent shift `pending`.
  - `GET /screenshots/pending` now returns the pending moderation queue for `verifier/advocate` roles.
  - `PATCH /screenshots/{id}/review` now updates screenshot review fields and synchronizes parent shift verification status (`verified` or `disputed`).
- Added storage configuration default in `fairgig-backend/.env.example`:
  - Added `SUPABASE_SCREENSHOT_BUCKET=earnings` for explicit bucket selection.
- Updated Phase tracker in `fairgig-backend/docs/phases.md`:
  - Marked all Phase 2 checklist items as complete.
- Completed live end-to-end Phase 2 validation against running API + Supabase DB/Storage:
  - Shift create/list/summary/city-median passed.
  - Screenshot upload/pending/review passed.
  - DB state verification confirmed screenshot status and parent shift status transitions.

## 2026-04-18 - Phase 1 Backend Foundation Implementation
- Name: Rehan Abrar
- Scope locked to backend only; no files under `fairgig-frontend/` were modified.
- Implemented pooled PostgreSQL lifecycle in `fairgig-backend/core/db.py`:
  - Added singleton asyncpg pool management via `get_pool()` and `close_pool()`.
  - Enforced `DATABASE_URL` presence with explicit runtime error for misconfiguration.
  - Kept compatibility wrappers (`connect_to_db`, `close_db_connection`) mapped to pooled lifecycle.
- Cleaned duplicate startup patterns in `fairgig-backend/core/main.py`:
  - Removed extra startup/shutdown DB hooks to avoid dual pool initialization paths.
  - Kept lifespan-based initialization as the single DB lifecycle path.
  - Updated default CORS allowlist to `http://localhost:3000` + production placeholder URL.
- Hardened auth behavior in `fairgig-backend/core/auth_middleware.py`:
  - Switched bearer auth to return 401 for missing credentials.
  - Added explicit guard for missing `SUPABASE_JWT_SECRET`.
  - Kept JWT validation with Supabase-compatible audience handling.
  - Improved role extraction fallback across user/app metadata.
- Implemented `POST /auth/setup-profile` persistence in `fairgig-backend/core/routers/auth.py`:
  - Replaced skeleton response with DB upsert into `profiles`.
  - Returns stable response shape: `{ id, role, status: "profile_saved" }`.
  - Uses JWT-derived role as trusted source to prevent request-body role escalation.
- Aligned anomaly service and backend env template defaults:
  - Updated `fairgig-backend/anomaly/main.py` CORS defaults to localhost + production placeholder.
  - Updated `fairgig-backend/.env.example` allowlist variables to same defaults.

## 2026-04-18 - Security Hardening Baseline
- Name: Rehan Abrar
- Added repository-level ignore policy in `.gitignore` to block env files, key/certificate files, and local secret directories from being committed.
- Hardened backend env template in `fairgig-backend/.env.example` with explicit runtime security variables (`ENVIRONMENT`, `STRICT_STARTUP`, `JWT_ALGORITHM`, CORS allowlists).
- Secured core API startup and CORS behavior in `fairgig-backend/core/main.py`:
  - CORS origins are now env-driven via `CORE_ALLOWED_ORIGINS`.
  - HTTP methods/headers are restricted to explicit allowlists.
  - Startup now fails in production-like modes when dependencies are unavailable.
- Secured anomaly service CORS behavior in `fairgig-backend/anomaly/main.py`:
  - Replaced wildcard CORS with env-driven allowlist via `ANOMALY_ALLOWED_ORIGINS`.
  - Restricted allowed methods and headers.
- Hardened JWT validation in `fairgig-backend/core/auth_middleware.py`:
  - Enforced presence of `SUPABASE_JWT_SECRET`.
  - Added required token claim checks for `sub` and `exp`.
  - Improved role extraction logic and bearer-token validation.
- Added backend security reference: `fairgig-backend/docs/security.md` with secret-handling, deployment, and verification checklist.

## 2026-04-18 - Backend-Only Workflow Instructions
- Name: Rehan Abrar
- Created backend docs folder: fairgig-backend/docs/.
- Added instruction file: fairgig-backend/docs/instructions.md.
- Logged the explicit rule to not modify anything inside fairgig-frontend/.
- Confirmed that future changes should be documented in this file with the name Rehan Abrar.

## 2026-04-18 - Initial FairGig Skeleton
- Read and mapped the full implementation plan in [PLAN.md](PLAN.md).
- Created backend scaffold in fairgig-backend with two FastAPI apps:
  - core app structure, routers, auth middleware, DB helper, requirements, and env example.
  - anomaly app structure, detector module, requirements, and health/detect endpoints.
- Created frontend scaffold in fairgig-frontend with:
  - Nuxt config, env example, API composable, Pinia stores, layouts, and route pages.
- Added starter placeholder logic in pages/routers so feature implementation can be layered in incrementally.
- Simplified frontend placeholders to avoid unresolved editor symbols before Nuxt dependencies are installed.

## 2026-04-18 - Phase 2 Shifts & Screenshots Implementation
- Name: Rehan Abrar
- Scope locked to backend only; no files under `fairgig-frontend/` were modified for this task.
- Implemented Phase 2 API endpoints in `fairgig-backend/core/routers/shifts.py`:
  - `POST /shifts` now inserts a shift row in PostgreSQL and returns persisted `shift_id`.
  - `GET /shifts` now returns the authenticated worker's shifts ordered by date.
  - `GET /shifts/summary` now computes `this_month`, `this_week`, `avg_hourly`, `avg_commission_pct`, and `total_shifts`.
  - `GET /shifts/city-median?platform=` now reads from `city_medians` using the worker profile's `city_zone` and `platform_category`.
  - Added non-blocking anomaly sidecar callback support after shift creation when `ANOMALY_SERVICE_URL` is configured.
- Implemented Phase 2 screenshot workflow in `fairgig-backend/core/routers/screenshots.py`:
  - `POST /screenshots/upload/{shift_id}` now validates shift ownership, uploads to Supabase Storage bucket `earnings`, records `earnings_screenshots`, and sets parent shift status to `pending`.
  - `GET /screenshots/pending` now returns pending review queue with joined shift/profile context.
  - `PATCH /screenshots/{id}/review` now validates review status, updates reviewer fields/timestamp, and syncs parent shift verification status.
- Updated Phase tracker in `fairgig-backend/docs/phases.md` by marking all Phase 2 checklist items complete.

## 2026-04-18 - Phase 2 E2E Validation + Error Handling Hardening
- Name: Mustafa
- Scope locked to backend only; no files under `fairgig-frontend/` were modified for this task.
- Hardened profile/shift write-path errors to avoid opaque 500s:
  - Updated `fairgig-backend/core/routers/auth.py` to catch `asyncpg.ForeignKeyViolationError` during `POST /auth/setup-profile` and return a clear 400 message when JWT `sub` is not present in Supabase `auth.users`.
  - Updated `fairgig-backend/core/routers/shifts.py` to catch `asyncpg.ForeignKeyViolationError` during `POST /shifts` and return a clear 400 message when worker profile is missing.
- Executed full real-user Phase 2 end-to-end test (not synthetic JWT-only IDs):
  - Created worker + verifier users in Supabase Auth via Admin API.
  - Ran `POST /auth/setup-profile` successfully for both roles.
  - Ran `POST /shifts` and confirmed created shift appears in `GET /shifts`.
  - Validated `GET /shifts/summary` returned totals and `GET /shifts/city-median` returned a valid response payload.
  - Uploaded proof via `POST /screenshots/upload/{shift_id}`.
  - Confirmed item appears in verifier queue via `GET /screenshots/pending`.
  - Reviewed item via `PATCH /screenshots/{id}/review` with status `verified`.
  - Verified parent shift `verification_status` changed to `verified`.
- Phase 2 gate is now verified end-to-end on the running local core API with live Supabase integration.
