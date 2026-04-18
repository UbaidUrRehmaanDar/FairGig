# FairGig Backend Security Baseline

This checklist prevents secret leakage and insecure defaults in local and deployed environments.

## 1) Secret Handling

- Keep real secrets only in local `.env` and deployment secret managers.
- Never commit real credentials, tokens, or private keys.
- Use `fairgig-backend/.env.example` as the only committed environment reference.
- Rotate any key immediately if it is ever exposed in commit history, chat, or screenshots.

## 2) Environment Variables

Required for secure backend operation:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `DATABASE_URL`
- `ANOMALY_SERVICE_URL`
- `ENVIRONMENT`
- `STRICT_STARTUP`
- `JWT_ALGORITHM`
- `CORE_ALLOWED_ORIGINS`
- `ANOMALY_ALLOWED_ORIGINS`

Notes:

- `STRICT_STARTUP=true` should be enabled in staging/production.
- `CORE_ALLOWED_ORIGINS` and `ANOMALY_ALLOWED_ORIGINS` must be explicit comma-separated allowlists.
- Avoid wildcard CORS origins in all environments.

## 3) Git Hygiene

A repository-level `.gitignore` now blocks:

- `.env` and `.env.*` (while allowing `.env.example`)
- private key and certificate formats (`*.pem`, `*.key`, `*.p12`, etc.)
- local secret directories (`secrets/`)

## 4) Deployment Rules

- Inject secrets through platform secret managers, not source control.
- Use least-privilege service keys where possible.
- Restrict API origins to trusted frontend domains only.
- Ensure TLS is enabled in all non-local environments.

## 5) Quick Verification Before Push

- Confirm no real values exist in tracked env files.
- Confirm CORS variables do not contain `*`.
- Confirm `SUPABASE_JWT_SECRET` is present and non-empty.
- Confirm no private key files are staged.
