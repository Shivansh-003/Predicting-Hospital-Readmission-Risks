# =============================================================================
# Hospital Readmission - HDFS Ingestion Script
# Ingests diabetic_data.csv into HDFS /readmission/raw/
# =============================================================================
[CmdletBinding()]
param(
    [Parameter()]
    [string]$CsvPath = "data/raw/diabetic_data.csv",

    [Parameter()]
    [string]$HdfsDir = "/readmission/raw",

    [Parameter()]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Hospital Readmission - Ingesting Dataset to HDFS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Verify local CSV file exists
Write-Host "`n[1/4] Verifying local dataset at $CsvPath..." -ForegroundColor Yellow
$resolvedCsvPath = Join-Path $rootDir $CsvPath
if (-not (Test-Path $resolvedCsvPath -PathType Leaf)) {
    Write-Error "Local CSV file not found at: $resolvedCsvPath"
    exit 1
}
$fileInfo = Get-Item $resolvedCsvPath
$fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
$fileSizeBytes = $fileInfo.Length
$fileName = $fileInfo.Name
Write-Host "[OK] Found CSV file: $fileName ($fileSizeMB MB, $fileSizeBytes bytes)" -ForegroundColor Green

# 2. Check NameNode container availability and safemode
Write-Host "`n[2/4] Checking NameNode service status..." -ForegroundColor Yellow
try {
    docker compose exec -T namenode hdfs dfsadmin -safemode leave | Out-Null
    Write-Host "[OK] Hadoop NameNode is responsive and Safemode is OFF." -ForegroundColor Green
} catch {
    Write-Error "Failed to connect to NameNode container. Ensure the cluster is running."
    exit 1
}

# 3. Create target HDFS directory if not exists
Write-Host "`n[3/4] Ensuring HDFS target directory exists: $HdfsDir..." -ForegroundColor Yellow
try {
    docker compose exec -T namenode hdfs dfs -mkdir -p $HdfsDir
    Write-Host "[OK] Target directory ready on HDFS: $HdfsDir" -ForegroundColor Green
} catch {
    Write-Error "Failed to create directory $HdfsDir in HDFS: $_"
    exit 1
}

# 4. Ingest CSV file into HDFS
$hdfsTargetPath = "$HdfsDir/$fileName"
Write-Host "`n[4/4] Uploading $fileName to $hdfsTargetPath..." -ForegroundColor Yellow

try {
    # Check if target file already exists in HDFS
    docker compose exec -T namenode hdfs dfs -test -e $hdfsTargetPath
    $fileExisted = ($LASTEXITCODE -eq 0)

    if ($fileExisted -and -not $Force) {
        Write-Host "Notice: File $hdfsTargetPath already exists in HDFS. Overwriting idempotently..." -ForegroundColor Yellow
    }

    # Staging to namenode container temporary location and putting into HDFS
    $containerTmpPath = "/tmp/$fileName"
    docker cp $resolvedCsvPath "namenode:$containerTmpPath"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy file into NameNode container."
    }

    docker compose exec -T namenode hdfs dfs -put -f $containerTmpPath $hdfsTargetPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to put file from container to HDFS."
    }

    # Clean up container temporary copy
    docker compose exec -T namenode rm -f $containerTmpPath

    # Verify uploaded file in HDFS
    $lsOutput = docker compose exec -T namenode hdfs dfs -ls $hdfsTargetPath
    Write-Host "[OK] HDFS File Status:" -ForegroundColor Green
    Write-Host $lsOutput -ForegroundColor Cyan

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "[OK] HDFS INGESTION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
} catch {
    Write-Error "[FAIL] Ingestion failed: $_"
    exit 1
}
