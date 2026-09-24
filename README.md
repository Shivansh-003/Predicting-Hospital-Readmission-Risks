# Hospital Readmission AI — Distributed Risk Prediction Platform

[![Status](https://img.shields.io/badge/Status-Infrastructure%20Validated-blue.svg)](#current-implementation-status)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linter](https://img.shields.io/badge/linter-ruff-orange.svg)](https://github.com/astral-sh/ruff)

> **Current Implementation Status:** **Project Foundation & Distributed Infrastructure (Validated)**  
> *Project foundation, configuration system, and Docker-based big data infrastructure (HDFS, Spark, Hive) are established and validated. Dataset acquisition, ML training, API, and dashboard components are planned/upcoming.*

---

## 1. Project Overview

**Hospital Readmission AI** is a distributed machine learning platform for predicting 30-day hospital readmission risk from electronic health records (EHR). The system provides an end-to-end distributed machine learning pipeline for predicting 30-day hospital readmission risk from structured EHR data, combining distributed data processing, SQL-based clinical feature engineering, comparative ML modeling, interpretable risk outputs, and an interactive analytics interface.

Rebuilt as a production-grade architecture, the project establishes a modular, reproducible, and containerized big data environment tailored for large-scale healthcare analytics.

---

## 2. Problem Statement

Unplanned hospital readmissions within 30 days of discharge are a critical quality metric for healthcare providers. High readmission rates reflect adverse health outcomes and impose substantial financial penalties (such as under the CMS Hospital Readmissions Reduction Program).

Accurate early risk stratification enables healthcare teams to proactively deliver targeted clinical interventions, coordinate post-discharge follow-ups, and allocate clinical resources effectively.

---

## 3. Architecture Overview

The production pipeline connects distributed storage, big data processing, ML training, serving, and user-facing analytics:

```
Raw EHR CSV / FHIR
        ↓
   Hadoop HDFS
        ↓
PySpark Data Preprocessing & Cleaning
        ↓
HiveQL Clinical Feature Engineering
        ↓
Spark ML Feature Pipeline (VectorAssembler / Encoders)
        ↓
Comparative Distributed Model Training
  ├── Logistic Regression
  ├── Random Forest
  ├── Decision Tree
  └── Gradient Boosted Trees
        ↓
Model Evaluation & Automatic Model Selection
        ↓
Model Registry & Versioning
        ↓
Explainability Engine (Risk Factor Attribution)
        ↓
FastAPI REST API Microservice
        ↓
Streamlit Clinical Dashboard & Patient Risk Simulator
```

---

## 4. Technology Stack

- **Distributed Storage & Computing:** Apache Hadoop HDFS, Apache Hive, Apache Spark (PySpark), Spark MLlib
- **Containerization & Orchestration:** Docker, Docker Compose
- **Programming & Core Frameworks:** Python (>= 3.10), PyYAML, Pydantic
- **API & Serving:** FastAPI, Uvicorn
- **Dashboard & Visualization:** Streamlit, Altair / Plotly
- **Quality, Linting & Testing:** Pytest, Ruff, Black, Mypy

---

## 5. Machine Learning Models & Evaluation

Four algorithms will be trained and benchmarked using Spark MLlib:

1. **Logistic Regression:** Linear baseline with calibrated probabilities.
2. **Decision Tree Classifier:** Non-linear rule-based baseline.
3. **Random Forest Classifier:** Bagged ensemble for variance reduction.
4. **Gradient Boosted Trees (GBT):** Sequential boosting for high discrimination.

### Evaluation Suite
- Metrics: **F1-Score (Primary)**, AUC-ROC, Recall / Sensitivity, Precision, Specificity, Accuracy, Confusion Matrix.
- Operational Benchmarks: Cluster training duration and inference latency per 1,000 records.

---

## 6. Project Structure

```
hospital-readmission-ai/
│
├── README.md                     # Project overview and instructions
├── LICENSE                       # MIT License
├── .gitignore                    # Comprehensive Git ignore rules
├── .env.example                  # Environment variable template
├── Makefile                      # Standardized development commands
├── pyproject.toml                # Project packaging and tool configuration
├── requirements.txt              # Core runtime dependencies
├── requirements-dev.txt          # Development, testing, and linting tools
│
├── docs/                         # Detailed architecture and design specifications
│   ├── PROJECT_SPEC.md           # System goals, requirements, and scope
│   ├── ARCHITECTURE.md           # Architectural layer diagrams and flows
│   ├── DEVELOPMENT_PLAN.md       # Engineering development roadmap
│   ├── DATA_DICTIONARY.md        # Conceptual dataset dictionary
│   ├── ML_SPEC.md                # ML algorithms and evaluation protocol
│   └── API_SPEC.md               # REST API endpoint definitions
│
├── config/                       # Centralized configuration
│   ├── config.yaml               # Project, storage, and logging settings
│   └── disease_profiles/         # Disease-specific clinical rule overlays
│       └── README.md
│
├── data/                         # Data storage (ignored in Git)
│   ├── raw/                      # Raw EHR datasets (e.g. UCI Diabetes)
│   ├── processed/                # Cleaned and partitioned parquet data
│   └── sample/                   # Small sample datasets for testing
│
├── docker/                       # Docker infrastructure configurations
│   ├── hadoop/                   # Hadoop / HDFS container setup
│   ├── spark/                    # Spark master & worker containers
│   └── hive/                     # Hive metastore & server setup
│
├── hive/                         # Hive DDL scripts & queries
│   ├── schema.hql                # Hive table definitions
│   ├── feature_views.hql         # Feature aggregation views
│   └── queries/                  # Analysis queries
│
├── src/                          # Application source code
│   ├── __init__.py
│   ├── preprocessing/            # PySpark cleaning and transformation
│   ├── features/                 # Spark ML feature extraction pipeline
│   ├── models/                   # Model definitions, training, & registry
│   ├── evaluation/               # Metric computation & model selection
│   ├── explainability/           # Risk factor contribution and ranking
│   └── utils/                    # Config loaders and helpers
│
├── api/                          # FastAPI serving microservice
│   └── README.md
│
├── dashboard/                    # Streamlit clinical dashboard & simulator
│   └── README.md
│
├── models/                       # Persisted model artifacts & checkpoints
├── outputs/                      # Evaluation reports, confusion matrices, logs
├── scripts/                      # Deployment and automation scripts
│   └── README.md
│
└── tests/                        # Comprehensive test suite
    ├── __init__.py
    ├── unit/                     # Fast unit tests
    └── integration/              # Integration and pipeline tests
```

---

## 7. Implementation Status

| Component / Layer | Status | Notes |
|---|---|---|
| **Project Foundation & Configuration** | Implemented | Directory layout, configuration system, toolchain, unit tests |
| **Distributed Data Infrastructure** | Implemented & Validated | Docker-based Hadoop HDFS, Spark Master/Workers, Hive Metastore & HiveServer2 |
| **Dataset Acquisition and Validation** | Upcoming | Automated download and schema verification of UCI Diabetes 130-US Hospitals dataset |
| **HDFS Data Ingestion** | Upcoming | Ingestion of raw EHR data into distributed HDFS storage |
| **Distributed Data Preprocessing** | Planned | PySpark cleaning, outlier handling, missing value imputation |
| **Hive Clinical Feature Engineering** | Planned | SQL feature views, comorbidity indices, utilization aggregates |
| **Spark ML Feature Pipeline** | Planned | Feature encoders, VectorAssembler, train/test split |
| **Model Training & Benchmarking** | Planned | Spark MLlib Logistic Regression, Decision Tree, Random Forest, GBT |
| **Model Evaluation & Selection** | Planned | Multi-metric evaluation and champion model selection based on F1-Score |
| **Model Registry & Versioning** | Planned | Checkpoint management, metadata logging, production tagging |
| **Explainability Engine** | Planned | Risk factor attribution, feature importance ranking |
| **Prediction Engine** | Planned | High-throughput batch and single-encounter risk inference |
| **FastAPI Model Serving Layer** | Planned | REST API microservice for real-time predictions |
| **Streamlit Analytics Dashboard** | Planned | Interactive clinical risk visualization and clinician interface |
| **Patient Risk Simulator** | Planned | Counterfactual "what-if" risk modification scenario testing |
| **FHIR & Disease Profiles** | Planned | FHIR bundle ingestion and specialized disease overlays |
| **Testing & Productionization** | Planned | End-to-end integration testing and validation suite |

---

## 8. Engineering Roadmap

1. **Project Foundation** — Core configuration, code structure, and development tooling. *(Implemented)*
2. **Distributed Data Infrastructure** — Containerized Big Data cluster (HDFS, Hive, Spark). *(Implemented & Validated)*
3. **Dataset Acquisition and Validation** — Acquisition and schema validation of clinical records. *(Upcoming)*
4. **HDFS Data Ingestion** — Transfer and staging of clinical records into HDFS. *(Planned)*
5. **Distributed Data Preprocessing** — Cleaning, normalization, and outlier treatment via PySpark. *(Planned)*
6. **Hive Clinical Feature Engineering** — Relational clinical feature extraction and aggregations. *(Planned)*
7. **Spark ML Feature Pipeline** — Vector transformations and feature scaling for ML. *(Planned)*
8. **Model Training** — Multi-algorithm distributed model training in Spark MLlib. *(Planned)*
9. **Model Evaluation** — Comprehensive performance assessment and ROC analysis. *(Planned)*
10. **Automatic Model Selection** — Data-driven champion model promotion. *(Planned)*
11. **Model Registry** — Model persistence, versioning, and lineage tracking. *(Planned)*
12. **Explainability** — Feature importance and local risk attribution. *(Planned)*
13. **Prediction Engine** — Standardized inference engine for single and batch predictions. *(Planned)*
14. **FastAPI Serving Layer** — High-performance REST API microservice. *(Planned)*
15. **Streamlit Analytics Dashboard** — Clinical dashboard for readmission risk monitoring. *(Planned)*
16. **Patient Risk Simulator** — Interactive counterfactual clinical risk simulation. *(Planned)*
17. **FHIR and Disease Profiles** — Interoperability with standard healthcare formats and disease-specific rules. *(Planned)*
18. **Testing and Productionization** — End-to-end testing, cluster validation, and health checks. *(Planned)*
19. **Documentation and Demonstration** — Comprehensive technical documentation and demonstration guides. *(Planned)*

---

## 9. Local Development Setup

### 9.1 Prerequisites
- Python >= 3.10
- Git

### 9.2 Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/hospital-readmission-ai.git
   cd hospital-readmission-ai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Verify environment and run test suite:**
   ```bash
   pytest
   ```

5. **Run code quality checks:**
   ```bash
   ruff check .
   black --check .
   mypy src tests
   ```
