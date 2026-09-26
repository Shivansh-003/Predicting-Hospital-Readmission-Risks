# =============================================================================
# Hospital Readmission - Run Spark ML Model Training Engine
# =============================================================================
[CmdletBinding()]
param(
    [Parameter()]
    [string]$Master = "spark://spark-master:7077",

    [Parameter()]
    [string]$OutputDir = "models"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Hospital Readmission - Running Spark ML Model Training Engine" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Verify Spark Master is active
Write-Host "`n[1/3] Checking Spark Master status..." -ForegroundColor Yellow
try {
    docker compose exec -T spark-master curl -s -f http://localhost:8080/ | Out-Null
    Write-Host "[OK] Spark Master is running and healthy." -ForegroundColor Green
} catch {
    Write-Error "Spark Master is not responding. Ensure the cluster is started with scripts/start_cluster.ps1."
    exit 1
}

# 2. Sync codebase into spark-master container
Write-Host "`n[2/3] Syncing model and feature modules into spark-master container..." -ForegroundColor Yellow
docker cp src spark-master:/opt/src
docker cp config spark-master:/opt/config
docker cp tests spark-master:/opt/tests
Write-Host "[OK] Source code synced to spark-master container." -ForegroundColor Green

# 3. Execute Model Training Job
Write-Host "`n[3/3] Submitting model training suite via spark-submit..." -ForegroundColor Yellow
$sparkCmd = "/spark/bin/spark-submit --master local[*] /opt/tests/test_model_training_spark.py"
docker compose exec -T -e PYTHONPATH=/opt spark-master sh -c "$sparkCmd"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Model training execution failed with exit code $LASTEXITCODE."
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "[OK] SPARK ML MODEL TRAINING EXECUTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
