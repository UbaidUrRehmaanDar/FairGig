# FairGig — Gig Worker Income & Rights Platform

## Overview

FairGig is a web-based platform designed to address financial transparency and labor rights challenges faced by gig workers in Pakistan. It enables workers to log, verify, and analyze their earnings across multiple platforms while providing advocates with tools to identify systemic unfairness.

The system is built to support non-technical users while maintaining data integrity, transparency, and actionable insights.

## Problem Statement

Gig workers often:

- Lack a unified record of their earnings
- Cannot verify platform deductions or commissions
- Have no formal proof of income
- Face sudden policy changes without transparency
- Lack a centralized community for grievances

FairGig solves these issues by providing structured logging, verification, analytics, and community-driven reporting.

## Key Features

### 1. Earnings Logger
Log shifts with:
- Platform
- Date
- Hours worked
- Gross earnings
- Deductions
- Net income
- Supports structured data entry for consistency

### 2. Screenshot Verification System
- Workers upload earnings screenshots
- Verifiers review submissions
- Status options: Verified, Flagged, Unverifiable
- Verification status is reflected in worker profiles

### 3. Worker Analytics Dashboard
- Weekly and monthly earnings trends
- Effective hourly rate tracking
- Platform commission monitoring
- Comparison with city-wide anonymized median

### 4. Income Certificate Generator
- Generates a clean, printable income report
- Based only on verified earnings
- Designed for: Banks, Landlords, Formal documentation

### 5. Grievance Board
**Workers can:**
- Post complaints
- Share platform issues

**Advocates can:**
- Tag and categorize complaints
- Escalate or resolve issues
- Supports collective visibility of problems

### 6. Advocate Analytics Panel
Aggregated insights including:
- Commission rate trends
- Income distribution by city zone
- Top complaint categories
- Workers with significant income drops

### 7. Anomaly Detection Service
Detects unusual patterns such as:
- High platform deductions
- Sudden income drops
- Zero net earnings
- Provides human-readable explanations

## System Architecture

The platform follows a modular service-oriented architecture with clear REST API boundaries.

### Core Services

| Service | Technology | Description |
|---------|-----------|-------------|
| Auth Service | Supabase Auth | JWT authentication and role management |
| Earnings Service | FastAPI | Shift logging, CRUD operations, verification tracking |
| Anomaly Service | FastAPI (Python) | Statistical anomaly detection |
| Grievance Service | Node.js | Complaint management |
| Analytics Service | FastAPI | Aggregated KPIs and insights |
| Certificate Renderer | Nuxt SSR | Printable income reports |

### Tech Stack

**Frontend**
- Nuxt 3 (Vue-based framework)
- Pinia (state management)
- Supabase client

**Backend**
- FastAPI (Python)
- Node.js (for grievance handling)
- AsyncPG for database access

**Database**
- PostgreSQL (via Supabase)

**Additional Tools**
- Supabase Storage (for screenshots)
- REST APIs for inter-service communication

## Database Design

### Schema
- Users (profiles)
- Shifts
- Screenshots
- Grievances

### Materialized Views
- City-wide median analytics

### Row-Level Security (RLS)
- Workers access only their own data
- Advocates access anonymized aggregates

## API Overview

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/shifts` | POST | Log a new shift |
| `/shifts` | GET | Retrieve worker shifts |
| `/shifts/summary` | GET | Earnings summary |
| `/screenshots/upload/{id}` | POST | Upload verification screenshot |
| `/grievances` | POST | Create complaint |
| `/grievances` | GET | View complaints |
| `/analytics/kpis` | GET | Advocate analytics |
| `/certificates/data` | GET | Generate certificate data |
| `/anomaly/detect` | POST | Detect anomalies |

## Anomaly Detection Logic

The anomaly service performs:
- Z-score analysis on deduction percentages
- Income drop detection (>20%)
- Detection of abnormal zero-net cases

Returns structured results with:
- Type
- Severity
- Explanation

## Setup Instructions

### Backend

```bash
cd fairgig-backend/core
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

```bash
cd fairgig-backend/anomaly
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd fairgig-frontend
npm install
npm run dev
```

## Environment Variables

### Backend
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_JWT_SECRET=
DATABASE_URL=
ANOMALY_SERVICE_URL=

### Frontend
SUPABASE_URL=
SUPABASE_KEY=
NUXT_PUBLIC_API_BASE=
NUXT_PUBLIC_ANOMALY_BASE=

## Demo Workflow

1. Worker logs a shift
2. Uploads screenshot for verification
3. Verifier reviews and approves
4. Worker sees verified earnings
5. Advocate monitors aggregated trends
6. Worker generates income certificate

## Design Decisions

- PostgreSQL chosen for strong relational support and analytical queries
- Materialized views used for efficient aggregated insights
- Supabase used to accelerate authentication and storage
- Services logically separated but optimized for rapid development

## Limitations

- Verification depends on human reviewers
- Anomaly detection is statistical, not deterministic
- Limited real-world dataset (demo seeded data)

## Future Improvements

- Automated screenshot parsing (OCR)
- Mobile-first interface
- Real-time notifications
- Advanced clustering for grievances
- Machine learning-based anomaly detection

## Conclusion

FairGig provides a scalable and practical solution to improve financial transparency, accountability, and collective awareness in the gig economy. It bridges the gap between individual workers and systemic insights, empowering both workers and advocates.
