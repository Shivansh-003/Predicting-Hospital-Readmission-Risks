# =============================================================================
# Hospital Readmission - Hive Feature Views Initialization Script
# Executes hive/feature_views.hql against HiveServer2
# =============================================================================
[CmdletBinding()]
param(
    [Parameter()]
    [string]$ViewsFile = "hive/feature_views.hql"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Hospital Readmission - Initializing Hive Feature Views" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Verify feature views file exists
Write-Host "`n[1/3] Verifying Hive feature views file at $ViewsFile..." -ForegroundColor Yellow
$resolvedViewsPath = Join-Path $rootDir $ViewsFile
if (-not (Test-Path $resolvedViewsPath -PathType Leaf)) {
    Write-Error "Hive feature views file not found at: $resolvedViewsPath"
    exit 1
}
Write-Host "[OK] Found feature views file: $ViewsFile" -ForegroundColor Green

# 2. Check HiveServer2 container
Write-Host "`n[2/3] Checking HiveServer2 service status..." -ForegroundColor Yellow
try {
    docker compose exec -T hive-server beeline -u "jdbc:hive2://localhost:10000" -n hive -p hive --silent=true -e "SHOW DATABASES;" | Out-Null
    Write-Host "[OK] HiveServer2 is reachable and responding." -ForegroundColor Green
} catch {
    Write-Error "Failed to connect to HiveServer2. Ensure the hive-server container is running and healthy."
    exit 1
}

# 3. Apply Hive feature views
Write-Host "`n[3/3] Applying feature views DDL from $ViewsFile..." -ForegroundColor Yellow
try {
    docker cp $resolvedViewsPath "hive-server:/tmp/feature_views.hql"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy feature views file into hive-server container."
    }

    docker compose exec -T hive-server beeline -u "jdbc:hive2://localhost:10000" -n hive -p hive -f /tmp/feature_views.hql
    if ($LASTEXITCODE -ne 0) {
        throw "Hive feature views DDL execution exited with code $LASTEXITCODE."
    }

    docker compose exec -T hive-server rm -f /tmp/feature_views.hql

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "[OK] HIVE FEATURE VIEWS INITIALIZED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
} catch {
    Write-Error "[FAIL] Hive feature views execution failed: $_"
    exit 1
}
