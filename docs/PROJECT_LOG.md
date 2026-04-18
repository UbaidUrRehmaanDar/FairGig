# Project Log

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
