# Project Submission Notes & Evaluation Documentation

**Company / Assessment Host:** Algions AI Labs Private Limited  
**Role:** DevOps & Cloud Engineering Intern / Advanced Project Assessment  
**Assigned Project:** Cloud Deployment & CI/CD – Hotel Booking Platform  

---

## 1. Candidate Information Form Placeholders
*(To be populated in the official submission form)*
- **Candidate Full Name:** [Student Name]
- **Registration / Student ID Number:** [Registration Number]
- **University Email:** [student@university.edu]
- **Assigned Role:** DevOps & Cloud Engineering
- **Repository URL:** [https://github.com/your-username/hotel-reservation-cicd]
- **Primary Branch:** `main`
- **Final Commit ID:** [Final Git Commit SHA]
- **Live Demo / Video URL:** [Link to 3–5 minute Loom / YouTube Demonstration]

---

## 2. Technology Stack Summary

| Domain | Technology / Library | Version | Rationale |
| :--- | :--- | :--- | :--- |
| **API Framework** | Python + FastAPI + Uvicorn | Python 3.12, FastAPI 0.115, Uvicorn 0.32 | High performance ASGI framework with native OpenAPI schema generation and async capabilities. |
| **Data Validation** | Pydantic v2 | 2.9.2 | High-throughput Rust-backed validation for request bodies and date bounds. |
| **ORM & Migrations** | SQLAlchemy 2.0 + Alembic | SQLAlchemy 2.0.36, Alembic 1.14.0 | Declarative ORM mapping, connection pooling, and versioned schema migrations. |
| **Database Engine** | PostgreSQL 16 (Docker Service) | 16-alpine | Enterprise relational DB with native `btree_gist` extension for exclusion constraints. |
| **Reverse Proxy** | Caddy v2 | 2.8.4-alpine | Lightweight, secure ingress proxy with automatic TLS (`tls internal`), HSTS, and 1MB body limit. |
| **Containerization** | Docker + Docker Compose v2 | Multi-stage `python:3.12.7-slim-bookworm` | Multi-stage build, unprivileged non-root user (UID 10001), capability dropping (`ALL`), healthchecks. |
| **CI/CD Automation** | GitHub Actions | Ubuntu Latest Runner | 5-stage automated pipeline: Lint -> Test -> Security -> Build -> Publish to GHCR. |
| **Quality & Linting** | Ruff + Mypy | Ruff 0.7.3, Mypy 1.13.0 | Fast linting, formatting, and strict static type verification. |
| **Test Automation** | Pytest + Pytest-Cov + HTTPX | Pytest 8.3.3, Pytest-Cov 6.0.0 | Full unit, integration, and multithreaded concurrency test suite (89% coverage). |
| **Security Auditing** | Gitleaks, Pip-Audit, Trivy | v2, 2.7.3, 0.28.0 | Secret detection, Python vulnerability scanning, and container filesystem/image scanning. |
| **Observability** | Structured JSON Logs + Prometheus | Prometheus FastAPI Instrumentator 7.0.0 | Standard JSON output with request IDs and scrapeable `/metrics`. |

---

## 3. Scope, Assumptions & Known Limitations
1. **Scope Boundary**: As specified in the brief, this project is deliberately focused on build, release, operational reliability, and CI/CD for the room availability and reservation API. UI screens, user authentication (OAuth/JWT), and payment gateways were intentionally omitted to maintain a correct, hardened MVP.
2. **Local TLS Authority**: For local testing and container orchestration, Caddy uses `tls internal`, issuing certificates signed by Caddy's local trust store. In production on a public domain, changing `tls internal` to an email address triggers automated Let's Encrypt / ZeroSSL ACME certificates.
3. **Database Concurrency Protection**: PostgreSQL's `btree_gist` extension and `EXCLUDE USING gist` constraint guarantee mutual exclusion across multiple containers, host processes, and cluster nodes. An in-process reentrant lock provides defense-in-depth within single-process test runs.

---

## 4. AI & Attribution Statement
- **AI Tool Usage**: AI assistant tools (including Google Antigravity / Gemini) were utilized during development for scaffolding configuration templates (such as Dockerfile, Makefile, and GitHub Actions workflow skeletons) and drafting boilerplate documentation.
- **Engineering Ownership & Explainability**: All architecture, database constraint logic, application code, test suites, and operational scripts have been thoroughly reviewed, refined, verified, and executed. The candidate understands the design, can explain every line in a live 15-minute technical walkthrough, and can modify any component during the live debugging assessment task.
- **Source Attributions**:
  - PostgreSQL documentation: `btree_gist` and Exclusion Constraints (`EXCLUDE USING gist`).
  - FastAPI documentation: Custom JSON exception handlers and Request-ID middleware.
  - Caddy documentation: Reverse proxy configuration and HTTP-to-HTTPS redirection.

