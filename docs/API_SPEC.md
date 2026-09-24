# API Specification — Hospital Readmission AI

> **Status:** Specification Only (Planned)  
> **Protocol:** HTTP / REST  
> **Data Format:** JSON  

---

## 1. Overview

The Hospital Readmission AI REST API provides programmatic access to real-time risk predictions, batch scoring jobs, model performance metrics, and patient risk profiles.

> [!NOTE]
> All endpoints documented below are **Planned** for implementation in the **FastAPI Serving Layer**.


---

## 2. Planned Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service liveness and cluster health check. |
| `GET` | `/api/v1/model` | Metadata, signature, and version of the currently active model. |
| `GET` | `/api/v1/metrics` | Evaluation metrics (F1, AUC-ROC, Recall, etc.) for the champion model. |
| `POST` | `/api/v1/predict` | Real-time single patient 30-day readmission risk inference. |
| `POST` | `/api/v1/batch-predict` | High-throughput batch inference on a list of patient encounters. |
| `GET` | `/api/v1/patients` | Paginated listing of patient risk records. |
| `GET` | `/api/v1/patients/{id}` | Detailed risk profile and feature attribution for a specific patient encounter. |

---

## 3. Endpoint Specifications (Planned)

### 3.1 `GET /health`
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development"
}
```

### 3.2 `GET /api/v1/model`
- **Response `200 OK`:**
```json
{
  "model_name": "RandomForestClassifier",
  "model_version": "v1.0.0",
  "framework": "Apache Spark MLlib",
  "target_metric": "f1",
  "trained_at": "2026-09-24T00:00:00Z"
}
```

### 3.3 `GET /api/v1/metrics`
- **Response `200 OK`:**
```json
{
  "f1_score": 0.684,
  "auc_roc": 0.742,
  "precision": 0.671,
  "recall": 0.698,
  "accuracy": 0.715,
  "specificity": 0.729
}
```

### 3.4 `POST /api/v1/predict`
- **Request Body:**
```json
{
  "encounter_id": "ENC100492",
  "patient_nbr": "PT88392",
  "age": "[60-70)",
  "gender": "Female",
  "time_in_hospital": 4,
  "num_lab_procedures": 45,
  "num_procedures": 1,
  "num_medications": 14,
  "number_outpatient": 0,
  "number_emergency": 1,
  "number_inpatient": 2,
  "diag_1": "250.02",
  "diag_2": "401.9",
  "diag_3": "428.0",
  "number_diagnoses": 7,
  "max_glu_serum": "None",
  "A1Cresult": ">8",
  "change": "Ch",
  "diabetesMed": "Yes"
}
```
- **Response `200 OK`:**
```json
{
  "encounter_id": "ENC100492",
  "readmission_prediction": 1,
  "readmission_risk_score": 0.742,
  "risk_tier": "High",
  "top_risk_factors": [
    { "feature": "number_inpatient", "contribution": 0.28 },
    { "feature": "number_emergency", "contribution": 0.19 },
    { "feature": "time_in_hospital", "contribution": 0.14 }
  ]
}
```

### 3.5 `POST /api/v1/batch-predict`
- **Request Body:**
```json
{
  "encounters": [
    { "encounter_id": "ENC101", "age": "[50-60)", "number_inpatient": 0 },
    { "encounter_id": "ENC102", "age": "[70-80)", "number_inpatient": 3 }
  ]
}
```
- **Response `200 OK`:**
```json
{
  "total_records": 2,
  "predictions": [
    { "encounter_id": "ENC101", "readmission_risk_score": 0.18, "risk_tier": "Low" },
    { "encounter_id": "ENC102", "readmission_risk_score": 0.81, "risk_tier": "Critical" }
  ]
}
```

### 3.6 `GET /api/v1/patients`
- **Query Parameters:** `page` (int), `limit` (int), `risk_tier` (string).
- **Response `200 OK`:** Array of patient summary cards with risk scores.

### 3.7 `GET /api/v1/patients/{id}`
- **Path Parameter:** `id` (encounter or patient ID).
- **Response `200 OK`:** Complete encounter history, risk trajectory, and explainability breakdown.
