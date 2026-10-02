# AERIS — Predictive Maintenance Decision-Support Platform

> **This system is a maintenance decision-support prototype. Predictions are not airworthiness or release-to-service decisions and are not validated for operational aircraft.**

## Quick Start

```bash
# 1. Generate secrets and certificates, build all images
make setup

# 2. Start all services
make up

# 3. Seed the database (migrate, generate data, ingest, train, score, recommend, create users)
make seed

# 4. Access the application
# Open https://localhost:8443 (accept self-signed certificate warning)
# Credentials: see secrets/demo_credentials.txt
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Client Browser                     │
│              https://localhost:8443                    │
└───────────────────────┬─────────────────────────────┘
                        │ TLS 1.2/1.3
                        ▼
┌─────────────────────────────────────────────────────┐
│              nginx (edge network)                     │
│  • Reverse proxy, TLS termination                    │
│  • Security headers (CSP, HSTS, etc.)                │
│  • Rate limiting (auth/api/upload zones)             │
│  • Static file serving (frontend)                    │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP (internal network only)
                        ▼
┌─────────────────────────────────────────────────────┐
│            FastAPI Backend (internal network)         │
│  • RESTful API (/api/v1/*)                           │
│  • Auth (Argon2id, JWT cookies, CSRF, RBAC)          │
│  • ML Pipeline (LightGBM, IsolationForest, SHAP)     │
│  • Planning engine, AaR Forecast, Evidence Passport  │
│  • No outbound internet access                       │
└───────────────────────┬─────────────────────────────┘
                        │ SQL (internal network only)
                        ▼
┌─────────────────────────────────────────────────────┐
│          PostgreSQL 16 (internal network)             │
│  • Least-privilege roles (migrator, app)             │
│  • Append-only audit_log with hash chain             │
│  • Immutable decisions and evidence_passports        │
│  • Field-level encryption (AES-256-GCM)              │
└─────────────────────────────────────────────────────┘
```

### Docker Networks
- **edge**: nginx only — exposed to host on port 8443
- **internal** (`internal: true`): backend + postgres — no outbound internet

## Available Make Targets

| Target | Description |
|--------|-------------|
| `make setup` | Generate secrets + certs, build all images |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make seed` | Full seed pipeline |
| `make train` | Train ML models |
| `make test` | Run all tests |
| `make lint` | Run linters |
| `make security-scan` | Run security scanning tools |
| `make demo-reset` | Full reset to demo state |
| `make tamper-demo` | Demonstrate tamper detection |
| `make logs` | Show service logs |

## Ports

| Service | Port | Access |
|---------|------|--------|
| nginx (HTTPS) | 8443 | Host-accessible |
| Backend | 8000 | Internal only |
| PostgreSQL | 5432 | Internal only |

## Data

All data is **synthetic and non-operational**. Every record is labelled with `data_source = SYNTHETIC_NON_OPERATIONAL`. The system does not contain, access, or process any classified, operational, or real defence data.

## Limitations

See [LIMITATIONS.md](LIMITATIONS.md) for a full list.
