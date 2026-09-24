-- =============================================================================
-- Hospital Readmission AI - Hive Schema Definition
-- Hive Clinical Feature Engineering
-- =============================================================================

CREATE DATABASE IF NOT EXISTS hospital_readmission;
USE hospital_readmission;

-- Raw / Stage Encounter Table (DDL to be finalized against validated dataset schema)
-- CREATE EXTERNAL TABLE IF NOT EXISTS encounters_raw (
--     encounter_id STRING,
--     patient_nbr STRING,
--     race STRING,
--     gender STRING,
--     age STRING,
--     admission_type_id INT,
--     discharge_disposition_id INT,
--     admission_source_id INT,
--     time_in_hospital INT,
--     num_lab_procedures INT,
--     num_procedures INT,
--     num_medications INT,
--     number_outpatient INT,
--     number_emergency INT,
--     number_inpatient INT,
--     diag_1 STRING,
--     diag_2 STRING,
--     diag_3 STRING,
--     number_diagnoses INT,
--     max_glu_serum STRING,
--     A1Cresult STRING,
--     change STRING,
--     diabetesMed STRING,
--     readmitted STRING
-- )
-- ROW FORMAT DELIMITED
-- FIELDS TERMINATED BY ','
-- STORED AS TEXTFILE
-- LOCATION '/data/raw/encounters';
