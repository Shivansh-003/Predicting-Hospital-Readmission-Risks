# =============================================================================
# Hospital Readmission - Hive Database & Table Initialization Script
# Executes hive/schema.hql against HiveServer2
# =============================================================================
[CmdletBinding()]
param(
    [Parameter()]
    [string]$SchemaFile = "hive/schema.hql"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Hospital Readmission - Initializing Hive Database and Tables" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Verify schema file exists
Write-Host "`n[1/3] Verifying Hive schema file at $SchemaFile..." -ForegroundColor Yellow
$resolvedSchemaPath = Join-Path $rootDir $SchemaFile
if (-not (Test-Path $resolvedSchemaPath -PathType Leaf)) {
    Write-Error "Hive schema file not found at: $resolvedSchemaPath"
    exit 1
}
Write-Host "[OK] Found schema file: $SchemaFile" -ForegroundColor Green

# 2. Check HiveServer2 container
Write-Host "`n[2/3] Checking HiveServer2 service status..." -ForegroundColor Yellow
try {
    docker compose exec -T hive-server beeline -u "jdbc:hive2://localhost:10000" -n hive -p hive --silent=true -e "SHOW DATABASES;" | Out-Null
    Write-Host "[OK] HiveServer2 is reachable and responding." -ForegroundColor Green
} catch {
    Write-Error "Failed to connect to HiveServer2. Ensure the hive-server container is running and healthy."
    exit 1
}

# 3. Apply Hive schema
Write-Host "`n[3/3] Applying schema DDL from $SchemaFile..." -ForegroundColor Yellow
try {
    docker cp $resolvedSchemaPath "hive-server:/tmp/schema.hql"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy schema file into hive-server container."
    }

    docker compose exec -T hive-server beeline -u "jdbc:hive2://localhost:10000" -n hive -p hive -f /tmp/schema.hql
    if ($LASTEXITCODE -ne 0) {
        throw "Hive DDL execution exited with code $LASTEXITCODE."
    }

    docker compose exec -T hive-server rm -f /tmp/schema.hql

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "[OK] HIVE DATABASE AND EXTERNAL TABLES INITIALIZED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
} catch {
    Write-Error "[FAIL] Hive schema execution failed: $_"
    exit 1
}
