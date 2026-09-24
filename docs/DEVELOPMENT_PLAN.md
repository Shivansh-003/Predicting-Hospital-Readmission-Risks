# Development Plan — Hospital Readmission AI

> **Status:** Project Foundation & Distributed Infrastructure (Validated)  
> **Target Version:** `2.0.0`

This document details the engineering development roadmap for building the Hospital Readmission AI platform.

---

## Engineering Roadmap Overview

| Module / Milestone | Status | Primary Dependencies |
|---|---|---|
| **Architecture and System Design** | Implemented | None |
| **Project Foundation and Environment** | Implemented | Architecture and System Design |
| **Distributed Data Infrastructure** | Implemented & Validated | Project Foundation and Environment |
| **Dataset Acquisition and Validation** | Upcoming | Project Foundation and Environment |
| **HDFS Data Ingestion** | Planned | Distributed Data Infrastructure, Dataset Acquisition |
| **Distributed Data Preprocessing** | Planned | HDFS Data Ingestion |
| **Hive Clinical Feature Engineering** | Planned | Distributed Data Preprocessing |
| **Spark ML Feature Pipeline** | Planned | Hive Clinical Feature Engineering |
| **Model Training** | Planned | Spark ML Feature Pipeline |
| **Model Evaluation** | Planned | Model Training |
| **Automatic Model Selection** | Planned | Model Evaluation |
| **Model Registry** | Planned | Automatic Model Selection |
| **Explainability** | Planned | Model Registry |
| **Prediction Engine** | Planned | Model Registry, Explainability |
| **FastAPI Serving Layer** | Planned | Prediction Engine |
| **Streamlit Analytics Dashboard** | Planned | FastAPI Serving Layer |
| **Patient Risk Simulation** | Planned | Streamlit Analytics Dashboard |
| **FHIR and Disease Profiles** | Planned | Hive Clinical Feature Engineering, Prediction Engine |
| **Testing and Productionization** | Planned | FastAPI Serving Layer, Streamlit Analytics Dashboard, Patient Risk Simulation |
| **Documentation and Demonstration** | Planned | Testing and Productionization |

---

## Detailed Milestone Breakdown

### 1. Architecture and System Design
- **Objective:** Establish system requirements, problem framing, and architectural boundary definitions.
- **Major Tasks:** Author specifications for system goals, functional/non-functional requirements, and interfaces.
- **Deliverables:** `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`.
- **Dependencies:** None.

### 2. Project Foundation and Environment
- **Objective:** Create a clean, reproducible, professional Python repository structure with strict linting, formatting, and configuration.
- **Major Tasks:** Set up directory tree, `pyproject.toml`, `requirements*.txt`, `Makefile`, `.gitignore`, `config/config.yaml`, and initial unit test.
- **Deliverables:** Validated repository skeleton, passing baseline unit tests, zero lint/formatting errors.
- **Dependencies:** Architecture and System Design.

### 3. Distributed Data Infrastructure
- **Objective:** Containerize Hadoop (HDFS), Hive (Metastore/Server2), and Apache Spark (Master/Workers).
- **Major Tasks:** Author Dockerfiles and `docker-compose.yml` for unified cluster provisioning and networking.
- **Deliverables:** `docker/` configurations, healthy cluster container orchestration, verification scripts.
- **Dependencies:** Project Foundation and Environment.

### 4. Dataset Acquisition and Validation
- **Objective:** Acquire, verify checksums, and profile the UCI Diabetes 130-US Hospitals dataset.
- **Major Tasks:** Download raw data, run exploratory data analysis (EDA), generate data schema baseline.
- **Deliverables:** Validated CSV in `data/raw/`, populated `docs/DATA_DICTIONARY.md`.
- **Dependencies:** Project Foundation and Environment.

### 5. HDFS Data Ingestion
- **Objective:** Implement automated batch ingestion of EHR files into distributed HDFS storage.
- **Major Tasks:** Write ingestion scripts to upload, partition, and verify files on HDFS namenode/datanode.
- **Deliverables:** HDFS data directories and transfer scripts in `scripts/`.
- **Dependencies:** Distributed Data Infrastructure, Dataset Acquisition and Validation.

### 6. Distributed Data Preprocessing
- **Objective:** Build distributed data cleaning and preparation pipelines using PySpark.
- **Major Tasks:** Handle missing/unknown tokens, filter terminal discharge records, encode target variable.
- **Deliverables:** `src/preprocessing/` modules and unit tests.
- **Dependencies:** HDFS Data Ingestion.

### 7. Hive Clinical Feature Engineering
- **Objective:** Implement HiveQL tables and feature views for clinical metrics.
- **Major Tasks:** Build comorbidity aggregations, utilization ratios, and diagnostic cluster queries in Hive.
- **Deliverables:** `hive/schema.hql`, `hive/feature_views.hql`, materialized feature tables.
- **Dependencies:** Distributed Data Preprocessing.

### 8. Spark ML Feature Pipeline
- **Objective:** Create a reproducible, serializable Spark ML feature extraction and assembly pipeline.
- **Major Tasks:** Implement `StringIndexer`, `OneHotEncoderEstimator`, and `VectorAssembler` stages.
- **Deliverables:** `src/features/` pipeline builders.
- **Dependencies:** Hive Clinical Feature Engineering.

### 9. Model Training
- **Objective:** Train four core machine learning classifiers on the engineered feature vectors.
- **Major Tasks:** Implement Logistic Regression, Random Forest, Decision Tree, and Gradient Boosted Trees trainers with hyperparameter grids.
- **Deliverables:** `src/models/` training routines.
- **Dependencies:** Spark ML Feature Pipeline.

### 10. Model Evaluation
- **Objective:** Compute comprehensive classification metrics for all trained models.
- **Major Tasks:** Evaluate Accuracy, Precision, Recall, F1, AUC-ROC, Sensitivity, Specificity, Confusion Matrix, and execution timings.
- **Deliverables:** `src/evaluation/` metric calculators and evaluation report outputs.
- **Dependencies:** Model Training.

### 11. Automatic Model Selection
- **Objective:** Programmatically determine the champion model based on configured target metrics (default: F1).
- **Major Tasks:** Implement model ranking, validation threshold enforcement, and automated champion designation.
- **Deliverables:** Automated selection module in `src/models/`.
- **Dependencies:** Model Evaluation.

### 12. Model Registry
- **Objective:** Standardize model serialization, versioning, and artifact tracking.
- **Major Tasks:** Save fitted Spark ML pipelines, parameters, metrics metadata, and schema signatures to `models/`.
- **Deliverables:** Model persistence and loading utilities.
- **Dependencies:** Automatic Model Selection.

### 13. Explainability
- **Objective:** Implement feature importance and patient-level risk factor attribution.
- **Major Tasks:** Compute global feature importance rankings and local risk driver breakdowns for clinical transparency.
- **Deliverables:** `src/explainability/` modules.
- **Dependencies:** Model Registry.

### 14. Prediction Engine
- **Objective:** Create a high-performance inference engine capable of scoring single records and batches.
- **Major Tasks:** Implement vectorization and model scoring wrapper for real-time and batch queries.
- **Deliverables:** Prediction engine class in `src/models/`.
- **Dependencies:** Model Registry, Explainability.

### 15. FastAPI Serving Layer
- **Objective:** Expose the prediction engine via a high-speed RESTful microservice.
- **Major Tasks:** Implement endpoints for health checks, model metadata, metrics, individual risk scoring, and batch jobs.
- **Deliverables:** `api/` application, Pydantic schemas, and API tests.
- **Dependencies:** Prediction Engine.

### 16. Streamlit Analytics Dashboard
- **Objective:** Build an interactive clinical web dashboard for healthcare practitioners.
- **Major Tasks:** Implement patient risk viewer, cohort explorer, feature importance charts, and model benchmark comparisons.
- **Deliverables:** `dashboard/` Streamlit application.
- **Dependencies:** FastAPI Serving Layer.

### 17. Patient Risk Simulation
- **Objective:** Enable counterfactual "what-if" analysis for clinical decision-making.
- **Major Tasks:** Interactive UI controls allowing clinicians to modify patient parameters (e.g., length of stay, medication adjustments) and observe real-time risk score changes.
- **Deliverables:** Simulator component integrated into Streamlit dashboard.
- **Dependencies:** Streamlit Analytics Dashboard.

### 18. FHIR and Disease Profiles
- **Objective:** Extend ingestion capabilities to FHIR JSON standards and disease-specific rule overlays.
- **Major Tasks:** Ingest FHIR Encounter/Condition resources and integrate `config/disease_profiles/`.
- **Deliverables:** FHIR adapters and customized disease profile weighting.
- **Dependencies:** Hive Clinical Feature Engineering, Prediction Engine.

### 19. Testing and Productionization
- **Objective:** Achieve comprehensive test coverage, load benchmarking, and hardening.
- **Major Tasks:** Full integration tests, end-to-end pipeline verification, API stress testing, and CI workflow scripts.
- **Deliverables:** Hardened test suite and performance benchmark reports.
- **Dependencies:** FastAPI Serving Layer, Streamlit Analytics Dashboard, Patient Risk Simulation.

### 20. Documentation and Demonstration
- **Objective:** Complete project documentation, operational runbooks, and demonstration artifacts.
- **Major Tasks:** Record demo walkthroughs, author deployment guide, compile project report.
- **Deliverables:** Final documentation, demo scripts, and release tags.
- **Dependencies:** Testing and Productionization.

