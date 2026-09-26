# =============================================================================
# Hospital Readmission - Run Model Evaluation Engine
# =============================================================================
[CmdletBinding()]
param(
    [Parameter()]
    [string]$Master = "spark://spark-master:7077",

    [Parameter()]
    [string]$OutputCsv = "outputs/model_comparison_report.csv"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Hospital Readmission - Running Model Evaluation Engine" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Verify Spark Master is running
Write-Host "`n[1/3] Checking Spark Master status..." -ForegroundColor Yellow
try {
    docker compose exec -T spark-master curl -s -f http://localhost:8080/ | Out-Null
    Write-Host "[OK] Spark Master is running and healthy." -ForegroundColor Green
} catch {
    Write-Error "Spark Master is not responding. Ensure the cluster is running with scripts/start_cluster.ps1."
    exit 1
}

# 2. Sync codebase into spark-master container
Write-Host "`n[2/3] Syncing evaluation and model modules into spark-master container..." -ForegroundColor Yellow
docker cp src spark-master:/opt/src
docker cp config spark-master:/opt/config
docker cp tests spark-master:/opt/tests
Write-Host "[OK] Source code synced to spark-master container." -ForegroundColor Green

# 3. Execute Model Evaluation Job
Write-Host "`n[3/3] Submitting model evaluation suite via spark-submit..." -ForegroundColor Yellow
$sparkCmd = "/spark/bin/spark-submit --master local[*] /opt/tests/test_evaluation_spark.py"
docker compose exec -T -e PYTHONPATH=/opt spark-master sh -c "$sparkCmd"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Model evaluation execution failed with exit code $LASTEXITCODE."
    exit 1
}

# 4. Copy generated comparison report back to host outputs/
Write-Host "`n[4/4] Copying evaluation report to host at $OutputCsv..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "outputs" | Out-Null
docker cp spark-master:/opt/outputs/model_comparison_report.csv outputs/model_comparison_report.csv -ErrorAction SilentlyContinue

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "[OK] MODEL EVALUATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
