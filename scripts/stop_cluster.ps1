# =============================================================================
# Hospital Readmission AI - Stop Big Data Cluster
# =============================================================================
[CmdletBinding()]
param(
    [switch]$Volumes
)

$ErrorActionPreference = "Stop"

Write-Host "Stopping Hospital Readmission AI Big Data Cluster..." -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Set-Location $rootDir

if ($Volumes) {
    Write-Host "Stopping containers and removing named volumes..." -ForegroundColor Yellow
    docker compose down -v
} else {
    Write-Host "Stopping containers (volumes preserved)..." -ForegroundColor Yellow
    docker compose down
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to stop Docker Compose services."
    exit 1
}

Write-Host "Cluster stopped successfully." -ForegroundColor Green
