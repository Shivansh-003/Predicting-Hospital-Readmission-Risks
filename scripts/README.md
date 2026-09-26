# Automation and Orchestration Scripts

This directory contains PowerShell and Python utility scripts for environment setup, data ingestion, pipeline orchestration, and cluster management.

## Available Scripts

- `start_cluster.ps1`: Starts the Docker big data cluster (Hadoop NameNode/DataNode, Spark Master/Workers, HiveServer2, PostgreSQL Metastore).
- `stop_cluster.ps1`: Stops the Docker cluster services.
- `status_cluster.ps1`: Reports the health and status of all cluster services.
- `verify_cluster.ps1`: Performs end-to-end sanity tests on HDFS, Spark, and Hive.
- `ingest_to_hdfs.ps1`: Verifies the local raw dataset (`diabetic_data.csv`) and ingests it into HDFS at `/readmission/raw/`.
- `init_hive.ps1`: Executes `hive/schema.hql` to initialize the `readmission` database and external tables.
- `run_preprocessing.ps1`: Submits the PySpark preprocessing pipeline to the Spark cluster and syncs the `readmission.patient_records_clean` Hive table.
- `init_feature_views.ps1`: Executes `hive/feature_views.hql` to initialize all clinical feature views in Apache Hive.
- `run_feature_pipeline.ps1`: Executes and validates the Spark ML feature transformation pipeline against `readmission.patient_features_view`.
- `train_models.ps1`: Trains all four Spark ML classification models and validates saved artifacts.
- `evaluate_models.ps1`: Evaluates all four models on the deterministic test partition and generates outputs/model_comparison_report.csv.
