# =============================================================================
# Hospital Readmission AI - Start Big Data Cluster
# =============================================================================
[CmdletBinding()]
param(
    [switch]$Wait
)

$ErrorActionPreference = "Stop"

Write-Host "Starting Hospital Readmission AI Big Data Cluster..." -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Set-Location $rootDir

docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Docker Compose services."
    exit 1
}

Write-Host "Services started. Current status:" -ForegroundColor Green
docker compose ps

Write-Host "`nCluster Web Interfaces:" -ForegroundColor Yellow
Write-Host " - Hadoop NameNode UI:  http://localhost:9870"
Write-Host " - Hadoop DataNode UI:  http://localhost:9864"
Write-Host " - Spark Master UI:     http://localhost:8080"
Write-Host " - Spark Worker 1 UI:   http://localhost:8081"
Write-Host " - Spark Worker 2 UI:   http://localhost:8082"
Write-Host " - HiveServer2 Port:    localhost:10000"
Write-Host " - Hive Metastore DB:   localhost:5432"
