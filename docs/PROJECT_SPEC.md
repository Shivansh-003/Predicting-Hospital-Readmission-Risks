# Project Specification — Hospital Readmission AI

> **Status:** Project Foundation & Distributed Infrastructure (Validated)  
> **Current Version:** `2.0.0`  
> **Target Audience:** Healthcare Engineers, Clinical Data Scientists, Hospital Administrators  

---

## 1. Executive Summary & Objective

**Hospital Readmission AI** is a distributed machine learning platform designed to predict 30-day all-cause hospital readmission risk from electronic health records (EHR). The project reconstructs and elevates a Big Data and ML pipeline into a production-grade, modular architecture leveraging Apache Spark, Apache Hive, PySpark, Spark MLlib, FastAPI, and Streamlit.

The primary objective is to enable clinical decision support by providing:
1. High-throughput distributed ingestion and batch ETL on raw EHR data.
2. Clinical feature extraction using SQL-based Hive views and PySpark transformations.
3. Comparative machine learning modeling across multiple algorithms to optimize prediction performance.
4. Interpretable risk outputs with factor attribution (e.g., comorbidity burden, previous utilization, inpatient stay length).
5. Interactive clinical interfaces (FastAPI REST API, Streamlit clinical dashboard, and patient risk simulation).

---

## 2. Problem Statement

Unplanned hospital readmissions within 30 days of discharge represent a major challenge for healthcare systems, resulting in adverse patient outcomes, elevated healthcare costs, and financial penalties under programs such as the Hospital Readmissions Reduction Program (HRRP).

Accurate early identification of high-risk patients enables targeted discharge planning, post-discharge follow-up, and timely clinical interventions. However, EHR data is characterized by high volume, class imbalance, complex diagnostic categorizations (ICD-9/ICD-10), and multi-modal clinical variables that require distributed computing architectures.

---

## 3. Scope & Status Boundaries

| Domain | Current Implementation Status | Planned Capabilities |
|---|---|---|
| **Repository & Environment** | Implemented (Structured repository, pyproject.toml, linting, tests, documentation) | Automated CI/CD, production deployment |
| **Big Data Infrastructure** | Implemented & Validated (Dockerized Hadoop/HDFS, Hive Metastore, Spark Master/Worker cluster) | Production cluster scaling |
| **Data Ingestion & Preprocessing** | Planned | Automated CSV/FHIR ingestion to HDFS, PySpark data cleaning & imputation |
| **Feature Engineering** | Planned (Hive DDL specifications ready) | HiveQL comorbidity aggregation, PySpark VectorAssembler pipeline |
| **Machine Learning** | Planned (Model specifications established) | Spark MLlib training (LR, RF, DT, GBT), cross-validation, automated selection |
| **Serving & API** | Planned (API specification established) | FastAPI asynchronous microservice with batch/single inference endpoints |
| **User Interface** | Planned (UI specifications established) | Streamlit clinical dashboard & patient risk simulator |


---

## 4. Functional Requirements (Planned)

1. **Distributed Data Ingestion (FR-1):** Ingest raw encounter datasets into HDFS with schema validation.
2. **Clinical Preprocessing & Cleaning (FR-2):** Handle missing values, filter non-viable encounter records (e.g., deceased discharge statuses), and standardize categorical fields.
3. **Clinical Feature Engineering (FR-3):** Derive clinical indicators including prior encounter frequency (emergency, inpatient, outpatient), admission urgency, medication changes, and ICD diagnosis clustering via Hive and PySpark.
4. **Multi-Model Training & Benchmarking (FR-4):** Train and evaluate Logistic Regression, Random Forest, Decision Tree, and Gradient Boosted Trees models using Spark MLlib.
5. **Automated Model Selection (FR-5):** Rank models against configurable metrics (F1-score primary, AUC-ROC, recall) and persist the champion model in the model registry.
6. **Interpretability & Risk Scoring (FR-6):** Calculate individualized readmission risk percentages and expose top contributing clinical features.
7. **REST API Interface (FR-7):** Expose endpoints for real-time risk scoring, batch inference, and model metadata.
8. **Interactive Clinical Dashboard (FR-8):** Provide clinical staff with cohort search, patient-level risk drilldown, and interactive "what-if" counterfactual simulation.

---

## 5. Non-Functional Requirements

- **Scalability:** Horizontal scaling of data processing and feature transformation using distributed Apache Spark nodes.
- **Reproducibility:** Hermetic configuration management via `config/config.yaml` and fully scripted Docker environments.
- **Code Quality:** Strict static analysis via Ruff, Black, and Mypy; comprehensive unit and integration test suites.
- **Low Latency Serving:** Sub-100ms single-patient prediction response time via FastAPI inference service.
- **Auditability:** Complete metadata tracking of trained models, parameters, training data versions, and evaluation metrics.

---

## 6. Target Users

- **Clinical Data Scientists:** Train, benchmark, and deploy Spark ML pipelines; inspect feature attributions and data distributions.
- **Hospital Administrators & Quality Teams:** Monitor readmission rates, evaluate model performance, and track HRRP risk metrics.
- **Physicians & Discharge Planners:** Review patient-specific risk scores and top risk factors to tailor discharge protocols.

---

## 7. Expected Inputs & Outputs

### Expected Inputs (Planned)
- Structured Electronic Health Record encounters (e.g., UCI Diabetes 130-US Hospitals dataset or FHIR Encounter resources).
- Fields include demographics, encounter duration, admission/discharge IDs, ICD diagnostic codes (diag_1, diag_2, diag_3), laboratory test frequencies, medication adjustments, and historical encounter counts.

### Expected Outputs (Planned)
- Binary classification: Readmission within 30 days (`<30` vs `>30` / `NO`).
- Calibrated probability risk score (`0.0%` – `100.0%`).
- Clinical risk tier: `Low`, `Moderate`, `High`, `Critical`.
- Local feature contribution attributions for decision transparency.
