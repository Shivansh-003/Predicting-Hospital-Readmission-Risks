-- =============================================================================
-- Hospital Readmission - Hive Feature Views
-- Hive Clinical Feature Engineering
-- =============================================================================

CREATE DATABASE IF NOT EXISTS readmission;
USE readmission;

-- -----------------------------------------------------------------------------
-- 1. Age Binning View (age_bin_view)
-- Derived from age_midpoint and demographic age intervals
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS readmission.age_bin_view;

CREATE VIEW IF NOT EXISTS readmission.age_bin_view AS
SELECT
    encounter_id,
    patient_nbr,
    age,
    age_midpoint,
    CASE
        WHEN age_midpoint < 30 THEN 'Under 30'
        WHEN age_midpoint BETWEEN 30 AND 64 THEN '30-64'
        ELSE '65 and older'
    END AS age_category,
    CASE
        WHEN age_midpoint >= 65 THEN 1
        ELSE 0
    END AS is_senior,
    CASE
        WHEN age_midpoint >= 75 THEN 1
        ELSE 0
    END AS is_geriatric
FROM readmission.patient_records_clean;

-- -----------------------------------------------------------------------------
-- 2. Length of Stay Category View (stay_category_view)
-- Categorizes hospitalization duration into Short (1-2), Medium (3-6), Long (7+)
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS readmission.stay_category_view;

CREATE VIEW IF NOT EXISTS readmission.stay_category_view AS
SELECT
    encounter_id,
    patient_nbr,
    time_in_hospital,
    CASE
        WHEN time_in_hospital BETWEEN 1 AND 2 THEN 'Short'
        WHEN time_in_hospital BETWEEN 3 AND 6 THEN 'Medium'
        ELSE 'Long'
    END AS stay_category,
    CASE
        WHEN time_in_hospital >= 7 THEN 1
        ELSE 0
    END AS is_long_stay,
    CASE
        WHEN time_in_hospital <= 2 THEN 1
        ELSE 0
    END AS is_short_stay
FROM readmission.patient_records_clean;

-- -----------------------------------------------------------------------------
-- 3. ICD-9 Diagnosis Grouping View (diagnosis_group_view)
-- Maps primary, secondary, and additional ICD-9 diagnostic codes into standard
-- clinical categories (Circulatory, Respiratory, Digestive, Diabetes, Injury,
-- Musculoskeletal, Genitourinary, Neoplasms, Other, Missing) and comorbidity flags.
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS readmission.diagnosis_group_view;

CREATE VIEW IF NOT EXISTS readmission.diagnosis_group_view AS
SELECT
    encounter_id,
    patient_nbr,
    diag_1,
    diag_2,
    diag_3,
    CASE
        WHEN diag_1 IS NULL OR trim(diag_1) = '' OR trim(diag_1) = '?' THEN 'Missing'
        WHEN diag_1 LIKE '250%' THEN 'Diabetes'
        WHEN (CAST(split(diag_1, '\\.')[0] AS INT) >= 390 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 459) OR split(diag_1, '\\.')[0] = '785' THEN 'Circulatory'
        WHEN (CAST(split(diag_1, '\\.')[0] AS INT) >= 460 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 519) OR split(diag_1, '\\.')[0] = '786' THEN 'Respiratory'
        WHEN (CAST(split(diag_1, '\\.')[0] AS INT) >= 520 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 579) OR split(diag_1, '\\.')[0] = '787' THEN 'Digestive'
        WHEN (CAST(split(diag_1, '\\.')[0] AS INT) >= 580 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 629) OR split(diag_1, '\\.')[0] = '788' THEN 'Genitourinary'
        WHEN (CAST(split(diag_1, '\\.')[0] AS INT) >= 710 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 739) THEN 'Musculoskeletal'
        WHEN (CAST(split(diag_1, '\\.')[0] AS INT) >= 140 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 239) THEN 'Neoplasms'
        WHEN (CAST(split(diag_1, '\\.')[0] AS INT) >= 800 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 999) THEN 'Injury'
        ELSE 'Other'
    END AS primary_diagnosis_group,
    CASE
        WHEN diag_2 IS NULL OR trim(diag_2) = '' OR trim(diag_2) = '?' THEN 'Missing'
        WHEN diag_2 LIKE '250%' THEN 'Diabetes'
        WHEN (CAST(split(diag_2, '\\.')[0] AS INT) >= 390 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 459) OR split(diag_2, '\\.')[0] = '785' THEN 'Circulatory'
        WHEN (CAST(split(diag_2, '\\.')[0] AS INT) >= 460 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 519) OR split(diag_2, '\\.')[0] = '786' THEN 'Respiratory'
        WHEN (CAST(split(diag_2, '\\.')[0] AS INT) >= 520 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 579) OR split(diag_2, '\\.')[0] = '787' THEN 'Digestive'
        WHEN (CAST(split(diag_2, '\\.')[0] AS INT) >= 580 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 629) OR split(diag_2, '\\.')[0] = '788' THEN 'Genitourinary'
        WHEN (CAST(split(diag_2, '\\.')[0] AS INT) >= 710 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 739) THEN 'Musculoskeletal'
        WHEN (CAST(split(diag_2, '\\.')[0] AS INT) >= 140 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 239) THEN 'Neoplasms'
        WHEN (CAST(split(diag_2, '\\.')[0] AS INT) >= 800 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 999) THEN 'Injury'
        ELSE 'Other'
    END AS secondary_diagnosis_group,
    CASE
        WHEN diag_3 IS NULL OR trim(diag_3) = '' OR trim(diag_3) = '?' THEN 'Missing'
        WHEN diag_3 LIKE '250%' THEN 'Diabetes'
        WHEN (CAST(split(diag_3, '\\.')[0] AS INT) >= 390 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 459) OR split(diag_3, '\\.')[0] = '785' THEN 'Circulatory'
        WHEN (CAST(split(diag_3, '\\.')[0] AS INT) >= 460 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 519) OR split(diag_3, '\\.')[0] = '786' THEN 'Respiratory'
        WHEN (CAST(split(diag_3, '\\.')[0] AS INT) >= 520 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 579) OR split(diag_3, '\\.')[0] = '787' THEN 'Digestive'
        WHEN (CAST(split(diag_3, '\\.')[0] AS INT) >= 580 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 629) OR split(diag_3, '\\.')[0] = '788' THEN 'Genitourinary'
        WHEN (CAST(split(diag_3, '\\.')[0] AS INT) >= 710 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 739) THEN 'Musculoskeletal'
        WHEN (CAST(split(diag_3, '\\.')[0] AS INT) >= 140 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 239) THEN 'Neoplasms'
        WHEN (CAST(split(diag_3, '\\.')[0] AS INT) >= 800 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 999) THEN 'Injury'
        ELSE 'Other'
    END AS additional_diagnosis_group,
    CASE
        WHEN diag_1 LIKE '250%' OR diag_2 LIKE '250%' OR diag_3 LIKE '250%' THEN 1
        ELSE 0
    END AS has_diabetes_diagnosis,
    CASE
        WHEN ((CAST(split(diag_1, '\\.')[0] AS INT) >= 390 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 459) OR split(diag_1, '\\.')[0] = '785')
          OR ((CAST(split(diag_2, '\\.')[0] AS INT) >= 390 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 459) OR split(diag_2, '\\.')[0] = '785')
          OR ((CAST(split(diag_3, '\\.')[0] AS INT) >= 390 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 459) OR split(diag_3, '\\.')[0] = '785')
        THEN 1
        ELSE 0
    END AS has_circulatory_diagnosis,
    CASE
        WHEN ((CAST(split(diag_1, '\\.')[0] AS INT) >= 460 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 519) OR split(diag_1, '\\.')[0] = '786')
          OR ((CAST(split(diag_2, '\\.')[0] AS INT) >= 460 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 519) OR split(diag_2, '\\.')[0] = '786')
          OR ((CAST(split(diag_3, '\\.')[0] AS INT) >= 460 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 519) OR split(diag_3, '\\.')[0] = '786')
        THEN 1
        ELSE 0
    END AS has_respiratory_diagnosis,
    CASE
        WHEN ((CAST(split(diag_1, '\\.')[0] AS INT) >= 520 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 579) OR split(diag_1, '\\.')[0] = '787')
          OR ((CAST(split(diag_2, '\\.')[0] AS INT) >= 520 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 579) OR split(diag_2, '\\.')[0] = '787')
          OR ((CAST(split(diag_3, '\\.')[0] AS INT) >= 520 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 579) OR split(diag_3, '\\.')[0] = '787')
        THEN 1
        ELSE 0
    END AS has_digestive_diagnosis,
    CASE
        WHEN ((CAST(split(diag_1, '\\.')[0] AS INT) >= 580 AND CAST(split(diag_1, '\\.')[0] AS INT) <= 629) OR split(diag_1, '\\.')[0] = '788')
          OR ((CAST(split(diag_2, '\\.')[0] AS INT) >= 580 AND CAST(split(diag_2, '\\.')[0] AS INT) <= 629) OR split(diag_2, '\\.')[0] = '788')
          OR ((CAST(split(diag_3, '\\.')[0] AS INT) >= 580 AND CAST(split(diag_3, '\\.')[0] AS INT) <= 629) OR split(diag_3, '\\.')[0] = '788')
        THEN 1
        ELSE 0
    END AS has_genitourinary_diagnosis
FROM readmission.patient_records_clean;

-- -----------------------------------------------------------------------------
-- 4. Prior Healthcare Utilization View (prior_admission_view)
-- Aggregates historical inpatient, outpatient, and emergency visit volumes.
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS readmission.prior_admission_view;

CREATE VIEW IF NOT EXISTS readmission.prior_admission_view AS
SELECT
    encounter_id,
    patient_nbr,
    COALESCE(number_inpatient, 0) AS number_inpatient,
    COALESCE(number_emergency, 0) AS number_emergency,
    COALESCE(number_outpatient, 0) AS number_outpatient,
    (COALESCE(number_inpatient, 0) + COALESCE(number_emergency, 0) + COALESCE(number_outpatient, 0)) AS total_prior_visits,
    CASE
        WHEN COALESCE(number_inpatient, 0) > 0 THEN 1
        ELSE 0
    END AS has_prior_inpatient,
    CASE
        WHEN COALESCE(number_emergency, 0) > 0 THEN 1
        ELSE 0
    END AS has_prior_emergency,
    CASE
        WHEN COALESCE(number_outpatient, 0) > 0 THEN 1
        ELSE 0
    END AS has_prior_outpatient,
    CASE
        WHEN (COALESCE(number_inpatient, 0) + COALESCE(number_emergency, 0) + COALESCE(number_outpatient, 0)) > 0 THEN 1
        ELSE 0
    END AS has_prior_visits,
    CASE
        WHEN (COALESCE(number_inpatient, 0) + COALESCE(number_emergency, 0) + COALESCE(number_outpatient, 0)) = 0 THEN 'None (0 visits)'
        WHEN (COALESCE(number_inpatient, 0) + COALESCE(number_emergency, 0) + COALESCE(number_outpatient, 0)) BETWEEN 1 AND 2 THEN 'Low (1-2 visits)'
        WHEN (COALESCE(number_inpatient, 0) + COALESCE(number_emergency, 0) + COALESCE(number_outpatient, 0)) BETWEEN 3 AND 5 THEN 'Moderate (3-5 visits)'
        ELSE 'High (6+ visits)'
    END AS utilization_tier,
    CASE
        WHEN COALESCE(number_inpatient, 0) = 0 THEN '0 visits'
        WHEN COALESCE(number_inpatient, 0) = 1 THEN '1 visit'
        ELSE '2+ visits'
    END AS inpatient_frequency_tier
FROM readmission.patient_records_clean;

-- -----------------------------------------------------------------------------
-- 5. Consolidated Patient Feature View (patient_features_view)
-- Joins cleaned encounter records with engineered clinical feature views.
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS readmission.patient_features_view;

CREATE VIEW IF NOT EXISTS readmission.patient_features_view AS
SELECT
    p.encounter_id,
    p.patient_nbr,
    p.race,
    p.gender,
    p.age,
    p.age_midpoint,
    a.age_category,
    a.is_senior,
    a.is_geriatric,
    p.admission_type_id,
    p.discharge_disposition_id,
    p.admission_source_id,
    p.time_in_hospital,
    s.stay_category,
    s.is_long_stay,
    s.is_short_stay,
    p.payer_code,
    p.medical_specialty,
    p.num_lab_procedures,
    p.num_procedures,
    p.num_medications,
    p.number_diagnoses,
    p.max_glu_serum,
    p.a1cresult,
    p.number_outpatient,
    p.number_emergency,
    p.number_inpatient,
    u.total_prior_visits,
    u.has_prior_inpatient,
    u.has_prior_emergency,
    u.has_prior_outpatient,
    u.has_prior_visits,
    u.utilization_tier,
    u.inpatient_frequency_tier,
    p.diag_1,
    p.diag_2,
    p.diag_3,
    d.primary_diagnosis_group,
    d.secondary_diagnosis_group,
    d.additional_diagnosis_group,
    d.has_diabetes_diagnosis,
    d.has_circulatory_diagnosis,
    d.has_respiratory_diagnosis,
    d.has_digestive_diagnosis,
    d.has_genitourinary_diagnosis,
    p.metformin,
    p.repaglinide,
    p.nateglinide,
    p.chlorpropamide,
    p.glimepiride,
    p.acetohexamide,
    p.glipizide,
    p.glyburide,
    p.tolbutamide,
    p.pioglitazone,
    p.rosiglitazone,
    p.acarbose,
    p.miglitol,
    p.troglitazone,
    p.tolazamide,
    p.examide,
    p.citoglipton,
    p.insulin,
    p.glyburide_metformin,
    p.glipizide_metformin,
    p.glimepiride_pioglitazone,
    p.metformin_rosiglitazone,
    p.metformin_pioglitazone,
    p.change,
    p.diabetesmed,
    p.insulin_flag,
    p.medication_change_flag,
    p.diabetes_med_flag,
    p.readmitted,
    p.readmission_target
FROM readmission.patient_records_clean p
INNER JOIN readmission.age_bin_view a ON p.encounter_id = a.encounter_id
INNER JOIN readmission.stay_category_view s ON p.encounter_id = s.encounter_id
INNER JOIN readmission.diagnosis_group_view d ON p.encounter_id = d.encounter_id
INNER JOIN readmission.prior_admission_view u ON p.encounter_id = u.encounter_id;
