# 3–5 Minute Video Demonstration Talking Script

This script is structured for recording the required 3–5 minute technical walkthrough video. It demonstrates all rubric requirements systematically.

---

## ⏱️ Video Timeline Overview
- **0:00 – 0:45**: Introduction & Architectural Design
- **0:45 – 1:30**: Automated CI/CD Pipeline & Security Scanning
- **1:30 – 2:30**: Deployed Stack, HTTPS Termination & Observability
- **2:30 – 3:30**: Concurrency Safety & Race Condition Acceptance Test
- **3:30 – 4:30**: Failure Injection, Self-Healing & Disaster Recovery (Restore Drill)
- **4:30 – 5:00**: Rollback Procedure & Conclusion

---

## 🎙️ Spoken Script & Actions

### 0:00 – 0:45: Introduction & Architectural Design
> *"Hello! I am presenting the Cloud Deployment and CI/CD project for the Hotel Reservation Platform.
> Our objective is not a large UI application, but a small, correct, highly available reservation API that is reproducibly buildable, observable, and recoverable with production-grade engineering practices.
> Looking at our architecture diagram in `docs/architecture.png`:
> Only our Caddy reverse proxy publishes ports 80 and 443 to the host, handling automatic HTTPS via `tls internal` and enforcing HTTP-to-HTTPS redirect, HSTS, and request size limits.
> The FastAPI service and PostgreSQL 16 database reside entirely on an isolated internal Docker bridge network. The application container runs as an unprivileged non-root user with UID 10001 and all capabilities dropped."*

### 0:45 – 1:30: CI/CD Pipeline & Security
> *(Show `.github/workflows/ci.yml`)*
> *"Our CI/CD pipeline triggers on every push and pull request. It executes in 5 distinct stages:
> First, Code Quality runs `ruff` linting and formatting, followed by `mypy` strict static type analysis.
> Second, our Automated Test suite spins up a PostgreSQL 16 service container, runs Alembic migrations to apply the database schema, and executes 19 pytest cases—including our concurrency test—producing an 89% coverage report.
> Third, our Security stage runs Gitleaks to detect committed secrets, Pip-Audit to verify dependencies against known CVEs, and Trivy to scan the filesystem.
> Fourth, Docker Buildx builds our multi-stage image with layer caching, scans the image with Trivy, and executes a smoke test via Docker Compose.
> Finally, upon merging to `main` or pushing a version tag, the image is published to GitHub Container Registry, and its immutable SHA256 digest is recorded."*

### 1:30 – 2:30: Live Deployed Stack & Observability
> *(Terminal: Run `make ps` and `curl -k https://localhost/health`)*
> *"Let's inspect our running deployment. Running `make ps` shows our three containers: `hotel_proxy`, `hotel_app`, and `hotel_db`, all marked healthy.
> Hitting `https://localhost/health` over HTTPS returns our liveness probe with the current semantic version and commit hash.
> Hitting `https://localhost/ready` verifies that our database connection pool is active and healthy.
> In our terminal logs, notice our structured JSON logging: every request generates a unique `X-Request-ID`, recording method, path, status code, and millisecond latency.
> We also expose Prometheus metrics at `/metrics` via the Prometheus FastAPI Instrumentator."*

### 2:30 – 3:30: Concurrency Acceptance Test (Double Booking Protection)
> *(Terminal: Run `bash scripts/concurrency_demo.sh`)*
> *"Now let's demonstrate Acceptance Test #1: preventing double bookings under concurrent race conditions.
> We fire 10 simultaneous conflicting reservation requests for the exact same room and date range using a multi-threaded client.
> Looking at the output:
> Exactly ONE request received `HTTP 201 Created` with unique reference `RSV-3V69PQPV`.
> All 9 other concurrent requests were rejected with `HTTP 409 Conflict`.
> This is enforced not just in Python application code, but in the PostgreSQL engine using a GiST exclusion constraint (`EXCLUDE USING gist`) and the `btree_gist` extension, operating on half-open date ranges `[check_in, check_out)`. This naturally permits back-to-back stays where checkout day equals next check-in day, while rejecting any partial or full overlap."*

### 3:30 – 4:30: Failure Detection & Restore Drill
> *(Terminal: Run `make failure-drill` then `make restore-drill`)*
> *"Next, let's observe platform resilience. Running `make failure-drill`:
> When the database is disrupted, the `/ready` probe immediately detects the failure, sheds traffic, and returns `HTTP 503 Service Unavailable`. As soon as the database recovers, `/ready` automatically recovers to `200 OK`.
> When the application container crashes, Docker's `restart: unless-stopped` policy automatically resurrects the service.
> Now let's test disaster recovery with `make restore-drill`:
> The script inserts a canary reservation, creates a compressed `pg_dump` backup with an accompanying SHA256 checksum, deliberately purges all reservations from the database, executes `pg_restore`, and proves that 100% of the data, including our canary reservation, is fully restored."*

### 4:30 – 5:00: Rollback Procedure & Conclusion
> *(Terminal: Run `make rollback-drill`)*
> *"Finally, we demonstrate zero-downtime release rollback. Running `make rollback-drill`:
> When a faulty release is deployed, our automated rollback script swaps the container to the previous immutable release tag (`v1.0.0`), queries `/health` to confirm the stable version is serving traffic, and supports database migration rollback via `alembic downgrade -1`.
> Everything in this repository is fully automated via Makefile targets, well-documented, and backed by verifiable audit evidence in the `evidence/` directory. Thank you!"*

