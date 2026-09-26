# =============================================================================
# Hospital Readmission - Verify Big Data Cluster
# =============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Verifying Big Data Infrastructure..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

# 1. Check Docker Containers
Write-Host "`n[1/4] Checking Docker Compose Services Status..." -ForegroundColor Yellow
$services = docker compose ps --format json | ConvertFrom-Json
$runningServices = $services | Where-Object { $_.State -eq "running" }
Write-Host "Found $($runningServices.Count) running services." -ForegroundColor Green

# 2. Verify HDFS
Write-Host "`n[2/4] Verifying Hadoop HDFS (NameNode and DataNode)..." -ForegroundColor Yellow
try {
    # Ensure safemode is off
    docker compose exec -T namenode hdfs dfsadmin -safemode leave
    
    # Create test directory
    docker compose exec -T namenode hdfs dfs -mkdir -p /verification_test
    
    # Write test file
    docker compose exec -T namenode sh -c "echo HDFS_Read_Write_Verified > /tmp/test_hdfs.txt && hdfs dfs -put -f /tmp/test_hdfs.txt /verification_test/test.txt"
    
    # Read test file back
    $hdfsContent = docker compose exec -T namenode hdfs dfs -cat /verification_test/test.txt
    Write-Host "HDFS Read Content: $hdfsContent" -ForegroundColor Green
    
    if ($hdfsContent -match "HDFS_Read_Write_Verified") {
        Write-Host "[OK] HDFS Verification PASSED" -ForegroundColor Green
    } else {
        throw "HDFS content mismatch."
    }
} catch {
    Write-Error "[FAIL] HDFS Verification FAILED: $_"
    exit 1
}

# 3. Verify Spark Cluster
Write-Host "`n[3/4] Verifying Spark Cluster (Master and Workers)..." -ForegroundColor Yellow
try {
    $sparkOutput = docker compose exec -T spark-master /spark/bin/spark-submit --master spark://spark-master:7077 --class org.apache.spark.examples.SparkPi /spark/examples/jars/spark-examples_2.12-3.1.1.jar 1
    Write-Host $sparkOutput
    if ($sparkOutput -match "Pi is roughly") {
        Write-Host "[OK] Spark Verification PASSED (SparkPi executed across cluster)" -ForegroundColor Green
    } else {
        throw "Spark computation verification failed."
    }
} catch {
    Write-Error "[FAIL] Spark Verification FAILED: $_"
    exit 1
}

# 4. Verify Hive and Metastore
Write-Host "`n[4/4] Verifying HiveServer2 and PostgreSQL Metastore..." -ForegroundColor Yellow
try {
    $hiveSql = "CREATE DATABASE IF NOT EXISTS test_db; USE test_db; DROP TABLE IF EXISTS verify_counts; CREATE TABLE verify_counts (id INT, item STRING); INSERT INTO verify_counts VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma'); SELECT count(*) FROM verify_counts;"
    $hiveOutput = docker compose exec -T hive-server beeline -u "jdbc:hive2://localhost:10000" -n hive -p hive --silent=true -e $hiveSql
    Write-Host $hiveOutput
    if ($hiveOutput -match "3") {
        Write-Host "[OK] Hive and Metastore Verification PASSED (3 rows inserted and counted)" -ForegroundColor Green
    } else {
        throw "Hive verification did not return expected count."
    }
} catch {
    Write-Error "[FAIL] Hive Verification FAILED: $_"
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "[OK] ALL CLUSTER VERIFICATION CHECKS PASSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
