# =============================================================================
# Hospital Readmission - Run PySpark Preprocessing Pipeline
# =============================================================================
[CmdletBinding()]
param(
    [Parameter()]
    [string]$InputHdfsPath = "hdfs://namenode:9000/readmission/raw/diabetic_data.csv",

    [Parameter()]
    [string]$OutputHdfsPath = "hdfs://namenode:9000/readmission/clean/patient_records_clean",

    [Parameter()]
    [string]$OutputHiveTable = "readmission.patient_records_clean"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Hospital Readmission - Running PySpark Preprocessing Pipeline" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Verify cluster is healthy
Write-Host "`n[1/4] Checking Spark Master and Workers status..." -ForegroundColor Yellow
$sparkStatus = docker compose exec -T spark-master curl -s -f http://localhost:8080/ | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Spark Master is not responding. Ensure the cluster is running with scripts/start_cluster.ps1."
    exit 1
}
Write-Host "[OK] Spark Master is running and healthy." -ForegroundColor Green

# 2. Copy src directory into spark-master container
Write-Host "`n[2/4] Syncing source code to spark-master container..." -ForegroundColor Yellow
docker compose exec -T spark-master rm -rf /opt/src /opt/config
docker cp src spark-master:/opt/src
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to copy src directory into spark-master container."
    exit 1
}
docker cp config spark-master:/opt/config
Write-Host "[OK] Code synced to spark-master container." -ForegroundColor Green

# 3. Submit PySpark Preprocessing Pipeline
Write-Host "`n[3/4] Submitting PySpark preprocessing job via spark-submit..." -ForegroundColor Yellow
$sparkSubmitCmd = "/spark/bin/spark-submit --master spark://spark-master:7077 --conf spark.driver.host=spark-master --conf spark.driver.bindAddress=0.0.0.0 /opt/src/preprocessing/pipeline.py --input-path $InputHdfsPath --output-path $OutputHdfsPath --output-table $OutputHiveTable"

docker compose exec -T -e PYTHONPATH=/opt spark-master sh -c "$sparkSubmitCmd"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] PySpark preprocessing job failed with exit code $LASTEXITCODE."
    exit 1
}
Write-Host "[OK] PySpark preprocessing job completed successfully." -ForegroundColor Green

# 4. Synchronize Hive clean table schema
Write-Host "`n[4/4] Updating Hive metastore catalog for $OutputHiveTable..." -ForegroundColor Yellow
docker cp hive/schema.hql hive-server:/tmp/schema.hql
docker compose exec -T hive-server beeline -u "jdbc:hive2://localhost:10000" -n hive -p hive -f /tmp/schema.hql | Out-Null
docker compose exec -T hive-server rm -f /tmp/schema.hql

Write-Host "[OK] Hive table $OutputHiveTable synchronized." -ForegroundColor Green

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "[OK] PREPROCESSING PIPELINE EXECUTION COMPLETED!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
