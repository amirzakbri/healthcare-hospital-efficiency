-- SQLite 3.35+. Grain: one source discharge row, NOT one distinct patient.
-- Visible duplicates are preserved because de-identification can collapse values.
DROP TABLE IF EXISTS clean_discharge;
CREATE TABLE clean_discharge AS
SELECT
    ROW_NUMBER() OVER (ORDER BY source_row_id) AS DischargeKey,
    source_row_id AS SourceRowId,
    permanent_facility_id AS HospitalKey,
    facility_name AS HospitalName,
    hospital_county AS HospitalCounty,
    CAST(discharge_year AS INTEGER) AS DischargeYear,
    apr_drg_code AS ConditionKey,
    apr_drg_description AS ConditionDescription,
    CAST(apr_severity_of_illness_code AS INTEGER) AS SeverityKey,
    apr_severity_of_illness AS Severity,
    age_group AS AgeGroup,
    payment_typology_1 AS PrimaryPayer,
    type_of_admission AS AdmissionType,
    patient_disposition AS Disposition,
    apr_risk_of_mortality AS MortalityRisk,
    emergency_department_indicator AS EDIndicator,
    length_of_stay AS SourceLOS,
    CASE WHEN length_of_stay = '120+' THEN 1 ELSE 0 END AS LOSCensored,
    CASE WHEN length_of_stay = '120+' THEN NULL
         WHEN CAST(length_of_stay AS INTEGER) BETWEEN 1 AND 119
         THEN CAST(length_of_stay AS INTEGER) END AS ExactLOS,
    CASE WHEN length_of_stay = '120+' THEN 120
         WHEN CAST(length_of_stay AS INTEGER) BETWEEN 1 AND 119
         THEN CAST(length_of_stay AS INTEGER) END AS BedDaysLowerBound,
    CostCentsParsed AS CostCents,
    ChargesCentsParsed AS ChargesCents
FROM raw_discharge;
CREATE UNIQUE INDEX IF NOT EXISTS ix_discharge ON clean_discharge(DischargeKey);
CREATE UNIQUE INDEX IF NOT EXISTS ix_source ON clean_discharge(SourceRowId);

-- Exact LOS only, known adult age groups and severity 1-4.
-- Benchmark strata: APR DRG x severity x age group.
DROP TABLE IF EXISTS hospital_stratum;
CREATE TABLE hospital_stratum AS
SELECT HospitalKey, ConditionKey, SeverityKey, AgeGroup,
       COUNT(*) AS HospitalN, SUM(ExactLOS) AS HospitalDays
FROM clean_discharge
WHERE ExactLOS IS NOT NULL AND SeverityKey BETWEEN 1 AND 4
  AND AgeGroup IN ('18-29','30-49','50-69','70 or Older')
GROUP BY HospitalKey, ConditionKey, SeverityKey, AgeGroup;

DROP TABLE IF EXISTS cohort_stratum;
CREATE TABLE cohort_stratum AS
SELECT ConditionKey, SeverityKey, AgeGroup,
       SUM(HospitalN) AS CohortN, SUM(HospitalDays) AS CohortDays,
       COUNT(*) AS HospitalsInStratum
FROM hospital_stratum
GROUP BY ConditionKey, SeverityKey, AgeGroup;

DROP TABLE IF EXISTS benchmark;
CREATE TABLE benchmark AS
SELECT h.HospitalKey, h.ConditionKey, h.SeverityKey, h.AgeGroup,
       c.CohortN-h.HospitalN AS PeerN,
       c.HospitalsInStratum-1 AS PeerHospitals,
       CASE WHEN c.CohortN-h.HospitalN >= 30 AND c.HospitalsInStratum-1 >= 3
            THEN 1.0*(c.CohortDays-h.HospitalDays)/(c.CohortN-h.HospitalN)
            ELSE NULL END AS ExpectedLOS
FROM hospital_stratum h
JOIN cohort_stratum c USING (ConditionKey, SeverityKey, AgeGroup);

DROP VIEW IF EXISTS discharge_model;
CREATE VIEW discharge_model AS
SELECT d.*,
       b.PeerN, b.PeerHospitals,
       CASE WHEN d.ExactLOS IS NOT NULL THEN b.ExpectedLOS END AS ExpectedLOS,
       CASE WHEN d.ExactLOS IS NOT NULL AND b.ExpectedLOS IS NOT NULL THEN 1 ELSE 0 END AS BenchmarkEligible,
       CASE WHEN d.LOSCensored=1 THEN '120+ days'
            WHEN d.ExactLOS <= 2 THEN '1-2 days'
            WHEN d.ExactLOS <= 5 THEN '3-5 days'
            WHEN d.ExactLOS <= 10 THEN '6-10 days'
            WHEN d.ExactLOS <= 20 THEN '11-20 days'
            WHEN d.ExactLOS <= 30 THEN '21-30 days'
            ELSE '31-119 days' END AS StayBand
FROM clean_discharge d
LEFT JOIN benchmark b USING (HospitalKey,ConditionKey,SeverityKey,AgeGroup);

DROP VIEW IF EXISTS hospital_summary;
CREATE VIEW hospital_summary AS
SELECT HospitalKey, HospitalName, HospitalCounty,
       COUNT(*) AS Discharges,
       COUNT(ExactLOS) AS ExactLOSDischarges,
       AVG(ExactLOS) AS AvgExactLOS,
       SUM(LOSCensored) AS CensoredDischarges,
       SUM(CostCents)/100.0 AS TotalEstimatedCost,
       AVG(CostCents)/100.0 AS AvgEstimatedCost,
       SUM(BenchmarkEligible) AS MatchedDischarges,
       1.0*SUM(BenchmarkEligible)/COUNT(*) AS BenchmarkCoverage,
       SUM(CASE WHEN BenchmarkEligible=1 THEN ExactLOS END) AS MatchedObservedDays,
       SUM(ExpectedLOS) AS MatchedExpectedDays,
       CASE WHEN SUM(BenchmarkEligible)>=30 THEN
           SUM(CASE WHEN BenchmarkEligible=1 THEN ExactLOS END)/SUM(ExpectedLOS)
       END AS LOSIndex
FROM discharge_model
GROUP BY HospitalKey, HospitalName, HospitalCounty;
