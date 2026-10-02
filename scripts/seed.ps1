# AERIS — Seed Database & ML Pipeline (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " AERIS — Database Migration & Pipeline Seeding" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Run migrations
Write-Host "`n[1/6] Running Alembic Migrations..." -ForegroundColor Yellow
docker compose exec -T backend python -m alembic upgrade head
docker compose exec -T backend python -c "from app.db.session import get_engine; from sqlalchemy import text; e=get_engine(); c=e.connect(); c.execute(text('SELECT protect_immutable_tables()')); c.commit(); c.close()"

# 2. Generate synthetic telemetry data
Write-Host "`n[2/6] Generating Synthetic Telemetry Dataset..." -ForegroundColor Yellow
docker compose exec -T backend python -m data_gen.generate_synthetic

# 3. Ingest data
Write-Host "`n[3/6] Ingesting Telemetry & Base Fleet..." -ForegroundColor Yellow
docker compose exec -T backend python -m app.db.seed --ingest

# 4. Train ML models
Write-Host "`n[4/6] Training LightGBM, RUL & Anomaly Models..." -ForegroundColor Yellow
docker compose exec -T backend python -m app.ml.train

# 5. Score fleet & generate recommendations
Write-Host "`n[5/6] Scoring Fleet & Running Planning Engine..." -ForegroundColor Yellow
docker compose exec -T backend python -m app.services.scoring --run
docker compose exec -T backend python -m app.services.planner --run

# 6. Create demo users
Write-Host "`n[6/6] Creating Demo Users..." -ForegroundColor Yellow
docker compose exec -T backend python -m app.db.seed --users

Write-Host "`n[+] Full database & ML pipeline seeding complete!" -ForegroundColor Green
Write-Host "[+] Log in at https://localhost:8443" -ForegroundColor Green
