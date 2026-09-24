# Data Dictionary (Conceptual) — Hospital Readmission AI

> **Status:** Conceptual Specification (Pre-Ingestion)  
> **Source Target:** UCI Diabetes 130-US Hospitals (1999–2008) Dataset  
> **Exact Schema Validation:** To be validated and finalized during **Dataset Acquisition and Validation**.

---

## 1. Dataset Overview

The project utilizes clinical encounter records from the **UCI Diabetes 130-US Hospitals** dataset (representing 10 years of clinical care across 130 US hospitals and integrated delivery networks).

### Known Source Characteristics
- **Volume:** Approximately 101,766+ clinical encounters.
- **Population:** Inpatient encounters satisfying criteria for diabetic patients with lengths of stay between 1 and 14 days.
- **Granularity:** Encounter-level records containing patient identifiers, admission details, clinical lab measurements, medication administrations, and diagnostic codes.
- **Target Variable:** Encounter readmission status, categorized into:
  - `<30` (Readmitted within 30 days — Positive class)
  - `>30` (Readmitted after 30 days — Negative class for 30-day target)
  - `NO` (No recorded readmission — Negative class)

---

## 2. Conceptual Feature Categories

The dataset conceptually contains the following thematic groupings:

1. **Patient Demographics:**
   - Age category, Gender, Race / Ethnicity.
2. **Admission & Discharge Attributes:**
   - Admission type (Emergency, Urgent, Elective), Admission source (Referral, Emergency Room, etc.), Discharge disposition (Home, Skilled Nursing Facility, etc.), Length of stay in hospital (days).
3. **Clinical & Utilization History:**
   - Number of outpatient visits in the preceding year.
   - Number of emergency room visits in the preceding year.
   - Number of inpatient admissions in the preceding year.
4. **Diagnoses & Comorbidities:**
   - Primary, secondary, and tertiary ICD-9 / ICD-10 diagnostic codes (`diag_1`, `diag_2`, `diag_3`).
   - Total number of active diagnoses entered into the system.
5. **Laboratory Tests & Clinical Metrics:**
   - Number of lab procedures performed.
   - Number of non-lab medical procedures performed.
   - Diagnostic tests (e.g., Glucose serum test results, HbA1c test results).
6. **Medications & Therapeutic Regimens:**
   - Total number of distinct medications administered.
   - Specific diabetes medications (e.g., insulin, metformin, sulfonylureas) with dosage adjustments (`Up`, `Down`, `Steady`, `No`).
   - Overall medication change indicator (`change`) and diabetes medication prescribed flag (`diabetesMed`).

---

## 3. Schema Validation & Evolution Notice

> [!IMPORTANT]
> The exact column names, data types, missing value tokens (e.g., `?`, `None`, empty strings), and category cardinality will be verified empirically during **Dataset Acquisition and Validation**. Once acquired, this document will be updated with the exact validated field-level schema and statistical summaries.

