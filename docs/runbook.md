# Operational Runbook & Incident Response Guide

## 1. Quick Operational Reference

| Operation | Command | Description |
| :--- | :--- | :--- |
| **Start Stack** | `make up` | Builds and starts DB, App, and Caddy with healthchecks |
| **Stop Stack** | `make down` | Gracefully terminates containers and cleans network state |
| **Restart Stack** | `make restart` | Restarts all active containers |
| **View Logs** | `make logs` | Streams aggregated structured JSON access logs |
| **Status / Health** | `make ps` | Displays container status and healthcheck convergence |
| **Run Seed Data** | `make seed` | Populates rooms and sample reservations idempotently |
| **Run Backup** | `make backup` | Generates timestamped, compressed DB dump with SHA256 |
| **Restore DB** | `make restore` | Restores database from latest verified backup |
| **Rollback Release** | `make rollback IMAGE_TAG=<tag>` | Deploys target previous image tag and verifies `/health` |

---

## 2. Standard Operating Procedures (SOPs)

### 2.1. Deployment & Release Management
```bash
# Step 1: Deploy new release using deploy script
bash scripts/deploy.sh ghcr.io/algions/hotel-reservation-api:v1.0.1

# Step 2: Verify zero-downtime healthcheck convergence
curl -k https://localhost/health
curl -k https://localhost/ready

# Step 3: Record deployed image digest
cat evidence/image-digest.txt
```

### 2.2. Database Backup & Disaster Recovery
```bash
# Create an on-demand snapshot
make backup

# Restore from a designated snapshot file
bash scripts/restore.sh backups/hotel_db_20261111_120000.dump

# Validate point-in-time recovery with automated drill
make restore-drill
```

### 2.3. Emergency Rollback Procedure
If a production deployment introduces critical defects:
```bash
# 1. Redeploy the last known stable image release
bash scripts/rollback.sh ghcr.io/algions/hotel-reservation-api:v1.0.0

# 2. If the failed release included an incompatible DB migration:
bash scripts/rollback.sh ghcr.io/algions/hotel-reservation-api:v1.0.0 --downgrade-db

# 3. Confirm restored status
curl -k https://localhost/health
```

---

## 3. Troubleshooting Matrix (Symptom → Check → Fix)

| Symptom | Root Cause Check | Remediation / Fix |
| :--- | :--- | :--- |
| **`/ready` returns HTTP 503** | `docker compose -f deploy/docker-compose.yml ps db`<br>`docker logs hotel_db` | Verify PostgreSQL is running. Check disk space. If stopped, run `docker compose up -d db`. Verify credentials in `.env`. |
| **App container crash-looping** | `docker logs hotel_app --tail 100`<br>`docker inspect hotel_app --format '{{.State.ExitCode}}'` | Check migration error (`alembic upgrade head`). Check DB reachability. If bad release deployed, trigger `bash scripts/rollback.sh`. |
| **Caddy returns 502 Bad Gateway** | `docker ps`<br>`docker logs hotel_proxy` | FastAPI app container is unhealthy or starting up. Ensure `hotel_app` passes `/ready` probe. Check internal Docker network `hotel_internal_net`. |
| **Disk space full on host** | `df -h`<br>`docker system df` | Prune dangling Docker images: `docker image prune -f`. Prune old backup files in `backups/` according to retention policy. |
| **Concurrent requests return 409** | Inspect structured JSON logs for `exclude_overlapping_confirmed_reservations` | This is **expected behavior** protecting against double bookings. Exactly one request confirmed (201); conflicting attempts safely rejected (409). |
| **Slow API queries (>500ms)** | Check Prometheus `/metrics` latency histograms | Inspect PostgreSQL query locks (`pg_stat_activity`). Verify indexes exist on `reservations(check_in, check_out, room_id)`. |

---

## 4. Incident Response Playbooks

### Incident 1: Database Outage (`hotel_db` Down)
1. **Detection**: Prometheus alert fires or `/ready` returns `HTTP 503 Service Unavailable`.
2. **Containment**: Caddy and FastAPI shed incoming reservation traffic while returning structured error JSON.
3. **Investigation**:
   ```bash
   docker logs hotel_db --tail 50
   ```
4. **Recovery**:
   ```bash
   docker compose -f deploy/docker-compose.yml up -d db
   # Monitor recovery:
   curl -k https://localhost/ready
   ```

### Incident 2: Bad Release Deployment
1. **Detection**: Elevated error rates on `/reservations` or unhandled exceptions in structured JSON logs.
2. **Immediate Action**:
   ```bash
   bash scripts/rollback.sh ghcr.io/algions/hotel-reservation-api:v1.0.0
   ```
3. **Verification**:
   ```bash
   curl -k https://localhost/health | grep '"version":"1.0.0"'
   ```

### Incident 3: Suspected Secret Leak
1. **Immediate Revocation**: Change PostgreSQL password immediately.
2. **Rotate Secrets**: Update `.env` or Docker Secret files with high-entropy replacements.
3. **Redeploy**: Restart DB and App services with new credentials.
4. **Audit**: Run Gitleaks across git history (`gitleaks detect --verbose`) to ensure no secrets were committed.

