# =============================================================================
# Hospital Readmission AI - Verify Big Data Cluster
# =============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Verifying Hospital Readmission AI Big Data Infrastructure..." -ForegroundColor Cyan
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
Write-Host "`n[2/4] Verifying Hadoop HDFS (NameNode & DataNode)..." -ForegroundColor Yellow
try {
    # Ensure safemode is off
    docker compose exec -T namenode hdfs dfsadmin -safemode leave
    
    # Create test directory
    docker compose exec -T namenode hdfs dfs -mkdir -p /verification_test
    
    # Write test file
    docker compose exec -T namenode sh -c 'echo "HDFS Read/Write Verified" > /tmp/test_hdfs.txt && hdfs dfs -put -f /tmp/test_hdfs.txt /verification_test/test.txt'
    
    # Read test file back
    $hdfsContent = docker compose exec -T namenode hdfs dfs -cat /verification_test/test.txt
    Write-Host "HDFS Read Content: $hdfsContent" -ForegroundColor Green
    
    if ($hdfsContent -match "HDFS Read/Write Verified") {
        Write-Host "✔ HDFS Verification PASSED" -ForegroundColor Green
    } else {
        throw "HDFS content mismatch."
    }
} catch {
    Write-Error "✖ HDFS Verification FAILED: $_"
    exit 1
}

# 3. Verify Spark Cluster
Write-Host "`n[3/4] Verifying Spark Cluster (Master & Workers)..." -ForegroundColor Yellow
try {
    $sparkScript = "from pyspark.sql import SparkSession; spark = SparkSession.builder.appName('VerifyCluster').master('spark://spark-master:7077').getOrCreate(); rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5]); total = rdd.reduce(lambda a, b: a + b); print('SPARK_COMPUTE_SUM=' + str(total)); assert total == 15, 'Sum must equal 15'; spark.stop()"
    $sparkOutput = docker compose exec -T spark-master python3 -c $sparkScript 2>&1
    Write-Host $sparkOutput
    if ($sparkOutput -match "SPARK_COMPUTE_SUM=15") {
        Write-Host "✔ Spark Verification PASSED (1 + 2 + 3 + 4 + 5 = 15)" -ForegroundColor Green
    } else {
        throw "Spark computation verification failed."
    }
} catch {
    Write-Error "✖ Spark Verification FAILED: $_"
    exit 1
}

# 4. Verify Hive & Metastore
Write-Host "`n[4/4] Verifying HiveServer2 & PostgreSQL Metastore..." -ForegroundColor Yellow
try {
    $hiveSql = "CREATE DATABASE IF NOT EXISTS test_db; USE test_db; DROP TABLE IF EXISTS verify_counts; CREATE TABLE verify_counts (id INT, item STRING); INSERT INTO verify_counts VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma'); SELECT count(*) FROM verify_counts;"
    $hiveOutput = docker compose exec -T hive-server beeline -u "jdbc:hive2://localhost:10000" -n hive -p hive --silent=true -e $hiveSql 2>&1
    Write-Host $hiveOutput
    if ($hiveOutput -match "3") {
        Write-Host "✔ Hive & Metastore Verification PASSED (3 rows inserted and counted)" -ForegroundColor Green
    } else {
        throw "Hive verification did not return expected count."
    }
} catch {
    Write-Error "✖ Hive Verification FAILED: $_"
    exit 1
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "✔ ALL CLUSTER VERIFICATION CHECKS PASSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
