# Acceptance Tests & Evidence Checklist

This document maps all five mandatory evaluation acceptance criteria directly to the command that proves them and the generated audit artifacts in `evidence/`.

| Acceptance Criterion | Verification Command | Evidence Artifact | Verification Status |
| :--- | :--- | :--- | :--- |
| **Acceptance Test #1**<br>Two concurrent conflicting requests must not both confirm.<br>*Under 10+ simultaneous conflicting requests, assert exactly one 201 and all remaining 409.* | `make test-concurrency`<br>`bash scripts/concurrency_demo.sh` | [`evidence/concurrency-demo.txt`](file:///c:/hotel%20booking%20website/evidence/concurrency-demo.txt)<br>[`evidence/test-output.txt`](file:///c:/hotel%20booking%20website/evidence/test-output.txt) | **PASSED**<br>(10 requests fired: 1 confirmed, 9 rejected with 409; 1 row committed in DB) |
| **Acceptance Test #2**<br>Clean clone build and start.<br>*Deterministic Docker build, multi-stage non-root container, persistent volume, and automatic migrations.* | `docker compose down -v && make up`<br>`make seed` | [`Dockerfile`](file:///c:/hotel%20booking%20website/Dockerfile)<br>[`deploy/docker-compose.yml`](file:///c:/hotel%20booking%20website/deploy/docker-compose.yml)<br>[`deploy/caddy/Caddyfile`](file:///c:/hotel%20booking%20website/deploy/caddy/Caddyfile) | **PASSED**<br>(Zero-touch initialization, automatic Alembic head migration, Caddy TLS termination) |
| **Acceptance Test #3**<br>CI/CD pipeline automation.<br>*Executes lint, formatting, static analysis, unit & concurrency tests, security scans, container build & publishes image.* | `gh workflow run ci.yml`<br>`make lint`<br>`make test` | [`.github/workflows/ci.yml`](file:///c:/hotel%20booking%20website/.github/workflows/ci.yml)<br>[`evidence/test-output.txt`](file:///c:/hotel%20booking%20website/evidence/test-output.txt)<br>[`evidence/coverage_html`](file:///c:/hotel%20booking%20website/evidence/coverage_html) | **PASSED**<br>(Ruff clean, Mypy strict clean, 19/19 pytest passed, 89% coverage, Gitleaks, Pip-Audit, Trivy) |
| **Acceptance Test #4**<br>Health, readiness & failure recovery.<br>*Show /health, /ready, structured JSON logs. Break database and show detection (503) & recovery (200). Kill app and show restart recovery.* | `make failure-drill`<br>`bash scripts/failure_drill.sh` | [`evidence/failure-drill.txt`](file:///c:/hotel%20booking%20website/evidence/failure-drill.txt)<br>[`evidence/health-capture.json`](file:///c:/hotel%20booking%20website/evidence/health-capture.json) | **PASSED**<br>(DB down: /ready returns 503; DB recovered: 200; App killed: recovered automatically) |
| **Acceptance Test #5**<br>Backup, restore and rollback drills.<br>*Point-in-time recovery (backup -> wipe -> restore -> verify canary). Rollback to previous image tag.* | `make restore-drill`<br>`make rollback-drill` | [`evidence/restore-drill.txt`](file:///c:/hotel%20booking%20website/evidence/restore-drill.txt)<br>[`evidence/rollback-drill.txt`](file:///c:/hotel%20booking%20website/evidence/rollback-drill.txt) | **PASSED**<br>(Canary reservation restored with 100% integrity; release rollback verified at /health) |

---

## Evidence Verification Details

### 1. Concurrency Protection Evidence (`evidence/concurrency-demo.txt`)
- Fired 10 simultaneous conflicting POST requests for Room 1 (`[2026-12-21, 2026-12-26)`).
- Outcome: **1 HTTP 201 Created** (Reference: `RSV-3V69PQPV`), **9 HTTP 409 Conflict**.
- Exactly one row persisted in the database table.

### 2. Failure & Recovery Evidence (`evidence/failure-drill.txt`)
- Baseline: `GET /ready` -> `HTTP 200 OK` `{"status": "ready", "database": "connected"}`.
- Simulated Outage: Database stopped -> `GET /ready` -> `HTTP 503 Service Unavailable`.
- Recovery: Database resumed -> `GET /ready` -> `HTTP 200 OK`.
- Process Crash: Container killed with SIGKILL -> Docker restart policy restored container to `healthy` state within seconds.

### 3. Restore Drill Evidence (`evidence/restore-drill.txt`)
- Created canary reservation: `RSV-CANARY-0127` for guest `Canary Tester`.
- Created database backup with SHA256 checksum: `e23b272d8c5d09da946b9c8e78bea826d8b76ae1ea78455833c2dcc151fa097c`.
- Simulated disaster: 100% of reservation records purged from database (`reservations = 0`).
- Restored from backup snapshot.
- Post-recovery validation: Row count restored, canary reservation `RSV-CANARY-0127` verified intact.

### 4. Rollback Drill Evidence (`evidence/rollback-drill.txt`)
- Initial release `v1.0.0` running.
- Deployed faulty release `v1.1.0-faulty`.
- Incident declared: automated rollback script `scripts/rollback.sh` executed.
- Verified `/health` confirms restored stable version `1.0.0` and commit SHA.

