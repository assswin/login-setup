# Production Launcher Script (Localhost)
# Builds the frontend and starts the unified FastAPI production server

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Building Frontend (Production Bundle)..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

npm --prefix frontend run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed. Aborting." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " Starting Production Server on Localhost..." -ForegroundColor Green
Write-Host " Access Web App: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host " API Docs:       http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host " Health Check:   http://127.0.0.1:8000/api/health" -ForegroundColor Green
Write-Host "=========================================`n" -ForegroundColor Green

& .\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
