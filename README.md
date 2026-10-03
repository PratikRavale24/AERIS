# AERIS - Aircraft Reliability & Intelligence System

![AERIS Banner](docs/assets/banner.png) <!-- Update this path if a banner is added -->

**Smart India Hackathon 2026** | **Problem Statement:** SIH26249

AERIS is an industry-grade, AI-driven predictive maintenance and fleet-availability decision-support platform. It integrates aircraft health telemetry, maintenance records, spare parts availability, and maintenance agency capacity to generate actionable, evidence-backed maintenance recommendations.

> **Note:** This is an advisory decision-support prototype. It does not replace human authorization or provide autonomous release-to-service decisions.

## Features

- **Fleet Overview**: Real-time KPI dashboard showing fleet availability, high-risk assets, and critical spare shortages.
- **Predictive Maintenance (PHM)**: Degradation anomaly detection and Remaining Useful Life (RUL) predictions powered by ensemble machine learning (LightGBM/XGBoost).
- **Human-in-the-loop Governance**: Cryptographically audited decisions with two-person override requirements and Ed25519 signature passports.
- **Spares & Capacity Matching**: Automatically validates parts availability and facility slot capacity against predicted maintenance needs.
- **Air-gapped Ready**: Designed to run securely in closed networks without external cloud dependencies.

## Architecture

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons.
- **Backend**: Python 3.12, FastAPI, Pydantic, SQLAlchemy.
- **Database**: PostgreSQL (synthetic benchmark data).
- **Security**: Argon2id hashing, strict HttpOnly/Secure session cookies, full CSRF protection, stateless JWTs, and RBAC implementation.
- **Proxy**: Nginx (Reverse proxy, rate limiting, and SSL termination).

## Local Development (Docker)

The fastest way to spin up the entire stack locally is via Docker Compose.

1. **Build the frontend production bundle:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Start the stack:**
   ```bash
   docker compose up -d --build
   ```

3. **Access the application:**
   - **App:** `https://localhost:8443`
   - **API Docs:** `http://localhost:8000/api/docs` (Note: Backend is securely proxied through Nginx).

> You will need to accept the self-signed certificate warning for local HTTPS.

## Deployment (Vercel / Cloud)

AERIS is configured for modern PaaS deployments.

### Frontend (Vercel)
The `frontend` directory is fully configured for Vercel deployment.
1. Connect the repository to Vercel.
2. Set the root directory to `frontend`.
3. Add the Environment Variable: `VITE_API_BASE_URL` pointing to your hosted backend URL.

### Backend (Render / Railway / AWS)
1. Deploy the `backend` directory using the provided `Dockerfile`.
2. Provide standard PostgreSQL credentials via environment variables (`POSTGRES_DB`, `POSTGRES_USER`, etc.) and supply securely generated keys for `JWT_SIGNING_KEY`, `AES_ENCRYPTION_KEY`, and `MODEL_HMAC_KEY`.

## Security Notes

This repository follows strict security guidelines:
- `.gitignore` prevents checking in sensitive keys, certificates, or environment files.
- The platform defaults to a *Deny-by-Default* authorization model.
- Demo passwords are auto-injected during the evaluation flow but rely on industry-standard hashing on the server side.

## License

This prototype is created for the Smart India Hackathon 2026. Data used is synthetic and representative. All rights reserved.
