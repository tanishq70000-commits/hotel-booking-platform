# Hotel Booking Platform — Cloud Deployment & CI/CD

[![CI/CD Pipeline](https://github.com/algions/hotel-reservation-api/actions/workflows/ci.yml/badge.svg)](https://github.com/algions/hotel-reservation-api/actions/workflows/ci.yml)
[![Docker Image](https://img.shields.io/badge/container-ghcr.io-blue.svg)](https://github.com/algions/hotel-reservation-api/pkgs/container/hotel-reservation-api)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-grade, highly reliable, and observable **Hotel Room Availability & Reservation API**. Built to demonstrate cloud deployment best practices, zero-downtime operations, deterministic containerization, hardened security, and strict concurrency safety against double bookings.

---

## Table of Contents
1. [Architecture & System Topology](#1-architecture--system-topology)
2. [Prerequisites](#2-prerequisites)
3. [Clean-Clone Quick Start](#3-clean-clone-quick-start)
4. [Environment Configuration](#4-environment-configuration)
5. [Port Map & Network Exposure](#5-port-map--network-exposure)
6. [API Endpoints & Usage (cURL Examples)](#6-api-endpoints--usage-curl-examples)
7. [Automated Testing & Concurrency Acceptance](#7-automated-testing--concurrency-acceptance)
8. [Code Quality & Security Scans](#8-code-quality--security-scans)
9. [CI/CD Pipeline Breakdown](#9-cicd-pipeline-breakdown)
10. [Deploy to VM / Production Procedure](#10-deploy-to-vm--production-procedure)
11. [Disaster Recovery: Backup & Restore](#11-disaster-recovery-backup--restore)
12. [Emergency Rollback Procedure](#12-emergency-rollback-procedure)
13. [Failure Recovery Drills](#13-failure-recovery-drills)
14. [Known Assumptions & Limitations](#14-known-assumptions--limitations)

---

## 1. Architecture & System Topology

The platform follows a zero-trust network topology where only the reverse proxy is exposed to external traffic:

```
[ Clients / Browsers ]
         │
         │ Ports 80 (HTTP -> 301) & 443 (HTTPS)
         ▼
┌────────────────────────────────────────────────────────┐
│ Caddy Reverse Proxy (hotel_proxy)                     │
│ - Automatic TLS ('tls internal')                       │
│ - HSTS, CSP, Frame Options, Sniff Guard                │
│ - 1MB Request Size Limit                               │
└────────────────────────┬───────────────────────────────┘
                         │ Internal Docker Network (hotel_internal_net)
                         ▼
┌────────────────────────────────────────────────────────┐
│ FastAPI Application Service (hotel_app:8000)          │
│ - Non-Root Execution (UID 10001, GID 10001)            │
│ - Capability Dropping (cap_drop: ALL)                  │
│ - Structured JSON Logs & X-Request-ID Correlation      │
│ - Liveness (/health), Readiness (/ready), Metrics      │
└────────────────────────┬───────────────────────────────┘
                         │ Internal SQLAlchemy Connection Pool (db:5432)
                         ▼
┌────────────────────────────────────────────────────────┐
│ PostgreSQL 16 Database (hotel_db:5432)                │
│ - Persistent Named Volume: hotel_db_data               │
│ - btree_gist extension                                 │
│ - EXCLUDE USING gist (Concurrent Overlap Protection)   │
└────────────────────────────────────────────────────────┘
```

Detailed architectural diagrams and flowcharts are available in [`docs/architecture.md`](docs/architecture.md) and [`docs/architecture.png`](docs/architecture.png).

---

## 2. Prerequisites
- **Docker Engine & Docker Compose v2**: Docker Desktop (Windows/macOS) or Docker Engine 24+ (Linux).
- **Python 3.12+** (for optional local non-container development).
- **Make** & **Bash** (standard on Linux/macOS; via Git Bash on Windows).

---

## 3. Clean-Clone Quick Start

Bring up the entire orchestrated stack with a single command from a clean clone:

```bash
# 1. Clone the repository
git clone https://github.com/algions/hotel-reservation-cicd.git
cd hotel-reservation-cicd

# 2. Build and launch all orchestrated containers
make up

# 3. Seed initial inventory (10 rooms across 4 categories + sample bookings)
make seed

# 4. Verify deployment health
curl -k https://localhost/health
curl -k https://localhost/ready
```

To stop and tear down the stack with all volumes preserved:
```bash
make down
```

---

## 4. Environment Configuration

Environment files are located in `deploy/env/`. **No secrets are ever committed to Git**; only `.example` templates are provided.

| Variable Name | Default / Example Value | Scope | Description |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | `development` / `production` | App | Environment runtime stage |
| `APP_VERSION` | `1.0.0` | App | Current semantic version tag |
| `COMMIT_SHA` | `dev-local` | App | Git commit SHA exposed in `/health` |
| `LOG_LEVEL` | `INFO` / `DEBUG` | App | Logging verbosity (JSON output) |
| `POSTGRES_DB` | `hotel_booking` | App, DB | PostgreSQL database name |
| `POSTGRES_USER` | `hotel_app_user` | App, DB | Least-privilege PostgreSQL user |
| `POSTGRES_PASSWORD` | *(Placeholder in example)* | App, DB | Database password (supports `_FILE`) |
| `DB_HOST` | `db` | App | Internal hostname of the DB service |
| `DB_PORT` | `5432` | App | Database port |
| `IMAGE_TAG` | `ghcr.io/...:v1.0.0` | Deploy | Pinned immutable container image tag |

---

## 5. Port Map & Network Exposure

| Service | Container Name | Internal Port | Host Port | Ingress Route | Exposure |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Caddy Proxy** | `hotel_proxy` | `80`, `443` | `80:80`, `443:443` | `https://localhost/` | **Public** |
| **FastAPI App** | `hotel_app` | `8000` | *None* | `http://app:8000` (Internal) | Internal Only |
| **PostgreSQL** | `hotel_db` | `5432` | *None* | `db:5432` (Internal) | Internal Only |

---

## 6. API Endpoints & Usage (cURL Examples)

All requests to Caddy's HTTPS endpoint can be tested with `curl -k` (to accept local self-signed CA):

### 6.1. Liveness & Readiness Checks
```bash
# Liveness probe (returns version & commit)
curl -k https://localhost/health
# Response: {"status":"healthy","version":"1.0.0","commit":"dev-local"}

# Readiness probe (verifies database connectivity)
curl -k https://localhost/ready
# Response: {"status":"ready","database":"connected"}
```

### 6.2. Query Room Availability
```bash
# Check available single rooms for a 5-night stay
curl -k "https://localhost/availability?check_in=2026-12-01&check_out=2026-12-06&room_type=single"
```

### 6.3. Create a Reservation
```bash
# Reserve Room 101
curl -k -X POST https://localhost/reservations \
  -H "Content-Type: application/json" \
  -d '{
    "guest_name": "Eleanor Vance",
    "guest_email": "eleanor.vance@example.com",
    "room_id": 1,
    "check_in": "2026-12-01",
    "check_out": "2026-12-06"
  }'

# Response: HTTP 201 Created
# {
#   "id": 3,
#   "reference": "RSV-9K3MZ48Q",
#   "room_id": 1,
#   "guest_name": "Eleanor Vance",
#   "guest_email": "eleanor.vance@example.com",
#   "check_in": "2026-12-01",
#   "check_out": "2026-12-06",
#   "status": "CONFIRMED"
# }
```

### 6.4. Fetch Reservation by Reference
```bash
curl -k https://localhost/reservations/RSV-9K3MZ48Q
```

### 6.5. Prometheus Metrics
```bash
curl -k https://localhost/metrics
```

---

## 7. Automated Testing & Concurrency Acceptance

Our test suite guarantees 100% adherence to domain rules and concurrency safety:
```bash
# Run full Pytest suite with coverage report
make test

# Run dedicated concurrency acceptance test
make test-concurrency

# Run live multi-threaded concurrency demo against running service
make concurrency-demo
```

### Concurrency Protection Breakdown:
When 10 simultaneous conflicting requests target the same room for overlapping dates:
- **Exactly 1 request** succeeds with `HTTP 201 Created`.
- **9 requests** are rejected with `HTTP 409 Conflict`.
- Verified at the database level via PostgreSQL's `EXCLUDE USING gist` constraint and `btree_gist` extension.
- Audit evidence recorded in [`evidence/concurrency-demo.txt`](evidence/concurrency-demo.txt).

---

## 8. Code Quality & Security Scans

Execute static analysis, formatting checks, and vulnerability scanning:
```bash
# 1. Lint and strict type check
make lint

# 2. Automatically fix formatting
make format

# 3. Scan production dependencies for known CVEs
make scan
```

- **Ruff**: Enforces PEP 8 standards, modern Python 3.12 syntax, import sorting, and code cleanups.
- **Mypy**: Strict static typing across all application models, schemas, and service layers.
- **Gitleaks**: Scans commit history for accidental credential leakage (`.gitleaks.toml`).
- **Pip-Audit**: Audits installed dependencies against the PyPA vulnerability database.
- **Trivy**: Comprehensive container image and filesystem scanner.

---

## 9. CI/CD Pipeline Breakdown

Our GitHub Actions workflow (`.github/workflows/ci.yml`) runs on all pushes and pull requests:

1. **`lint`**: Runs `ruff check`, `ruff format --check`, and `mypy` strict type checking.
2. **`test`**: Spins up a `postgres:16` service container, executes Alembic migrations, runs 19 pytest test cases including the concurrency suite, and uploads test and coverage artifacts.
3. **`security`**: Executes Gitleaks for secret detection, Pip-Audit for dependencies, and Trivy for filesystem vulnerabilities.
4. **`build`**: Builds the multi-stage Docker image with layer caching, scans the image with Trivy for HIGH/CRITICAL issues, and executes a Docker Compose smoke test.
5. **`publish`**: *(On main branch / tags only)* Pushes the immutable image to GitHub Container Registry (GHCR), captures the image digest, and outputs a job summary.

---

## 10. Deploy to VM / Production Procedure

Deploying onto a staging or production VM is fully automated via `scripts/deploy.sh`:

```bash
# Deploy a pinned immutable image release to the host
bash scripts/deploy.sh ghcr.io/algions/hotel-reservation-api:v1.0.0
```

The deployment script:
1. Pulls the target immutable container image by tag.
2. Applies `deploy/docker-compose.prod.yml` overrides (enforcing resource limits and removing local bind mounts).
3. Executes a zero-downtime rolling container replacement.
4. Awaits healthcheck convergence on `/ready`.
5. Records the deployed image SHA256 digest in `evidence/image-digest.txt`.

---

## 11. Disaster Recovery: Backup & Restore

### Point-in-Time Recovery
```bash
# Generate a timestamped, custom-format database backup
make backup

# Restore the database from the newest backup artifact
make restore

# Run an automated point-in-time recovery drill
make restore-drill
```

The restore drill validates:
1. Inserts a canary reservation (`RSV-CANARY-XXXX`).
2. Creates an encrypted backup with a companion `.sha256` checksum.
3. Simulates catastrophic failure by deleting all records from the database.
4. Restores from backup and proves 100% data recovery.
5. Audit evidence recorded in [`evidence/restore-drill.txt`](evidence/restore-drill.txt).

---

## 12. Emergency Rollback Procedure

If a deployed release introduces regressions:
```bash
# Roll back to the previous stable release tag
bash scripts/rollback.sh ghcr.io/algions/hotel-reservation-api:v1.0.0

# If database schema changes need reversion:
bash scripts/rollback.sh ghcr.io/algions/hotel-reservation-api:v1.0.0 --downgrade-db
```

Run the automated rollback simulation drill:
```bash
make rollback-drill
```
Audit evidence recorded in [`evidence/rollback-drill.txt`](evidence/rollback-drill.txt).

---

## 13. Failure Recovery Drills

Validate platform self-healing and observability under failure conditions:
```bash
make failure-drill
```
Demonstrates:
- **Database Outage**: When PostgreSQL is stopped, `/ready` immediately returns `HTTP 503 Service Unavailable`, logging structured errors. When PostgreSQL restarts, `/ready` self-heals to `HTTP 200 OK`.
- **Application Crash**: When the app process is terminated, Docker's `restart: unless-stopped` policy restarts the container and returns it to `healthy` state.
- Audit evidence recorded in [`evidence/failure-drill.txt`](evidence/failure-drill.txt).

---

## 14. Known Assumptions & Limitations
- **Local TLS**: Caddy issues local certificates using `tls internal`. In production on a public DNS record, replacing `tls internal` with a valid domain name switches automatically to Let's Encrypt ACME.
- **Scope Boundary**: As instructed in the assessment brief, this project focuses strictly on build, release, operational reliability, and CI/CD for the reservation API. UI screens, customer payment processing, and JWT authentication were intentionally not built.

