# =============================================================================
# Hospital Readmission AI - Check Big Data Cluster Status
# =============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"

Write-Host "Hospital Readmission AI Big Data Cluster Status:" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Set-Location $rootDir

docker compose ps

Write-Host "`nContainer Resource Usage:" -ForegroundColor Cyan
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
