-- =============================================================================
-- Hospital Readmission - Hive Database & External Tables Schema
-- =============================================================================

CREATE DATABASE IF NOT EXISTS readmission;
USE readmission;

-- 1. Raw External Table (Delimited CSV)
DROP TABLE IF EXISTS readmission.patient_records;

CREATE EXTERNAL TABLE IF NOT EXISTS readmission.patient_records (
    encounter_id BIGINT COMMENT 'Unique identifier of an encounter',
    patient_nbr BIGINT COMMENT 'Unique identifier of a patient',
    race STRING COMMENT 'Race/ethnicity of the patient',
    gender STRING COMMENT 'Gender of the patient',
    age STRING COMMENT 'Age grouped in 10-year intervals',
    weight STRING COMMENT 'Weight in pounds',
    admission_type_id INT COMMENT 'Integer identifier for admission type',
    discharge_disposition_id INT COMMENT 'Integer identifier for discharge disposition',
    admission_source_id INT COMMENT 'Integer identifier for admission source',
    time_in_hospital INT COMMENT 'Integer number of days between admission and discharge',
    payer_code STRING COMMENT 'Integer identifier for payer code',
    medical_specialty STRING COMMENT 'Specialty of admitting physician',
    num_lab_procedures INT COMMENT 'Number of lab tests performed during the encounter',
    num_procedures INT COMMENT 'Number of procedures performed during the encounter',
    num_medications INT COMMENT 'Number of distinct generic medications administered',
    number_outpatient INT COMMENT 'Number of outpatient visits in year preceding encounter',
    number_emergency INT COMMENT 'Number of emergency visits in year preceding encounter',
    number_inpatient INT COMMENT 'Number of inpatient visits in year preceding encounter',
    diag_1 STRING COMMENT 'Primary diagnosis code',
    diag_2 STRING COMMENT 'Secondary diagnosis code',
    diag_3 STRING COMMENT 'Additional secondary diagnosis code',
    number_diagnoses INT COMMENT 'Number of diagnoses entered to the system',
    max_glu_serum STRING COMMENT 'Glucose serum test result',
    a1cresult STRING COMMENT 'A1C test result',
    metformin STRING COMMENT 'Metformin prescription status',
    repaglinide STRING COMMENT 'Repaglinide prescription status',
    nateglinide STRING COMMENT 'Nateglinide prescription status',
    chlorpropamide STRING COMMENT 'Chlorpropamide prescription status',
    glimepiride STRING COMMENT 'Glimepiride prescription status',
    acetohexamide STRING COMMENT 'Acetohexamide prescription status',
    glipizide STRING COMMENT 'Glipizide prescription status',
    glyburide STRING COMMENT 'Glyburide prescription status',
    tolbutamide STRING COMMENT 'Tolbutamide prescription status',
    pioglitazone STRING COMMENT 'Pioglitazone prescription status',
    rosiglitazone STRING COMMENT 'Rosiglitazone prescription status',
    acarbose STRING COMMENT 'Acarbose prescription status',
    miglitol STRING COMMENT 'Miglitol prescription status',
    troglitazone STRING COMMENT 'Troglitazone prescription status',
    tolazamide STRING COMMENT 'Tolazamide prescription status',
    examide STRING COMMENT 'Examide prescription status',
    citoglipton STRING COMMENT 'Citoglipton prescription status',
    insulin STRING COMMENT 'Insulin prescription status',
    glyburide_metformin STRING COMMENT 'Glyburide-metformin prescription status',
    glipizide_metformin STRING COMMENT 'Glipizide-metformin prescription status',
    glimepiride_pioglitazone STRING COMMENT 'Glimepiride-pioglitazone prescription status',
    metformin_rosiglitazone STRING COMMENT 'Metformin-rosiglitazone prescription status',
    metformin_pioglitazone STRING COMMENT 'Metformin-pioglitazone prescription status',
    change STRING COMMENT 'Change in diabetic medications',
    diabetesMed STRING COMMENT 'Diabetic medication prescribed',
    readmitted STRING COMMENT '30-day readmission status'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs:///readmission/raw/'
TBLPROPERTIES ("skip.header.line.count"="1");

-- 2. Cleaned and Encoded Preprocessed Table (Parquet)
DROP TABLE IF EXISTS readmission.patient_records_clean;

CREATE EXTERNAL TABLE IF NOT EXISTS readmission.patient_records_clean (
    encounter_id BIGINT COMMENT 'Unique identifier of an encounter',
    patient_nbr BIGINT COMMENT 'Unique identifier of a patient',
    race STRING COMMENT 'Race/ethnicity of the patient',
    gender STRING COMMENT 'Gender of the patient',
    age STRING COMMENT 'Age grouped in 10-year intervals',
    weight STRING COMMENT 'Weight in pounds',
    admission_type_id INT COMMENT 'Integer identifier for admission type',
    discharge_disposition_id INT COMMENT 'Integer identifier for discharge disposition',
    admission_source_id INT COMMENT 'Integer identifier for admission source',
    time_in_hospital INT COMMENT 'Integer number of days between admission and discharge',
    payer_code STRING COMMENT 'Integer identifier for payer code',
    medical_specialty STRING COMMENT 'Specialty of admitting physician',
    num_lab_procedures INT COMMENT 'Number of lab tests performed during the encounter',
    num_procedures INT COMMENT 'Number of procedures performed during the encounter',
    num_medications INT COMMENT 'Number of distinct generic medications administered',
    number_outpatient INT COMMENT 'Number of outpatient visits in year preceding encounter',
    number_emergency INT COMMENT 'Number of emergency visits in year preceding encounter',
    number_inpatient INT COMMENT 'Number of inpatient visits in year preceding encounter',
    diag_1 STRING COMMENT 'Primary diagnosis code',
    diag_2 STRING COMMENT 'Secondary diagnosis code',
    diag_3 STRING COMMENT 'Additional secondary diagnosis code',
    number_diagnoses INT COMMENT 'Number of diagnoses entered to the system',
    max_glu_serum STRING COMMENT 'Glucose serum test result',
    a1cresult STRING COMMENT 'A1C test result',
    metformin STRING COMMENT 'Metformin prescription status',
    repaglinide STRING COMMENT 'Repaglinide prescription status',
    nateglinide STRING COMMENT 'Nateglinide prescription status',
    chlorpropamide STRING COMMENT 'Chlorpropamide prescription status',
    glimepiride STRING COMMENT 'Glimepiride prescription status',
    acetohexamide STRING COMMENT 'Acetohexamide prescription status',
    glipizide STRING COMMENT 'Glipizide prescription status',
    glyburide STRING COMMENT 'Glyburide prescription status',
    tolbutamide STRING COMMENT 'Tolbutamide prescription status',
    pioglitazone STRING COMMENT 'Pioglitazone prescription status',
    rosiglitazone STRING COMMENT 'Rosiglitazone prescription status',
    acarbose STRING COMMENT 'Acarbose prescription status',
    miglitol STRING COMMENT 'Miglitol prescription status',
    troglitazone STRING COMMENT 'Troglitazone prescription status',
    tolazamide STRING COMMENT 'Tolazamide prescription status',
    examide STRING COMMENT 'Examide prescription status',
    citoglipton STRING COMMENT 'Citoglipton prescription status',
    insulin STRING COMMENT 'Insulin prescription status',
    glyburide_metformin STRING COMMENT 'Glyburide-metformin prescription status',
    glipizide_metformin STRING COMMENT 'Glipizide-metformin prescription status',
    glimepiride_pioglitazone STRING COMMENT 'Glimepiride-pioglitazone prescription status',
    metformin_rosiglitazone STRING COMMENT 'Metformin-rosiglitazone prescription status',
    metformin_pioglitazone STRING COMMENT 'Metformin-pioglitazone prescription status',
    change STRING COMMENT 'Change in diabetic medications',
    diabetesMed STRING COMMENT 'Diabetic medication prescribed',
    readmitted STRING COMMENT '30-day readmission status',
    age_midpoint INT COMMENT 'Numeric midpoint of age interval',
    insulin_flag INT COMMENT 'Binary flag for active insulin regimen (1=Up/Down/Steady, 0=No)',
    medication_change_flag INT COMMENT 'Binary flag for diabetic medication alteration (1=Ch, 0=No)',
    diabetes_med_flag INT COMMENT 'Binary flag for diabetic medication prescription (1=Yes, 0=No)',
    readmission_target INT COMMENT 'Binary target for 30-day readmission (1=<30, 0=>30 or NO)'
)
STORED AS PARQUET
LOCATION 'hdfs:///readmission/clean/patient_records_clean';
