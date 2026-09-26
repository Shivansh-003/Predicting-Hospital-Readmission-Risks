# =============================================================================
# Hospital Readmission - Run Spark ML Feature Pipeline
# =============================================================================
[CmdletBinding()]
param(
    [Parameter()]
    [string]$HiveView = "readmission.patient_features_view",

    [Parameter()]
    [string]$Master = "spark://spark-master:7077"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Hospital Readmission - Running Spark ML Feature Pipeline" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Verify Spark cluster is running
Write-Host "`n[1/3] Checking Spark Master status..." -ForegroundColor Yellow
try {
    docker compose exec -T spark-master curl -s -f http://localhost:8080/ | Out-Null
    Write-Host "[OK] Spark Master is running and healthy." -ForegroundColor Green
} catch {
    Write-Error "Spark Master is not responding. Start the cluster with scripts/start_cluster.ps1."
    exit 1
}

# 2. Sync codebase into spark-master container
Write-Host "`n[2/3] Syncing feature modules into spark-master container..." -ForegroundColor Yellow
docker cp src spark-master:/opt/src
docker cp config spark-master:/opt/config
docker cp tests spark-master:/opt/tests
Write-Host "[OK] Source code synced to spark-master container." -ForegroundColor Green

# 3. Execute feature pipeline runner
Write-Host "`n[3/3] Submitting feature transformation job via spark-submit..." -ForegroundColor Yellow
$sparkCmd = "/spark/bin/spark-submit --master local[*] /opt/tests/test_feature_pipeline_spark.py"
docker compose exec -T -e PYTHONPATH=/opt spark-master sh -c "$sparkCmd"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Feature pipeline execution failed with exit code $LASTEXITCODE."
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "[OK] SPARK ML FEATURE PIPELINE EXECUTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
