# Project Log

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
