-- Run statements separately in healthcare.sqlite. Results are also in analysis/.

-- 1. Which clinical groups account for the most discharges and estimated cost?
SELECT ConditionDescription, COUNT(*) AS Discharges,
       ROUND(AVG(ExactLOS),2) AS AvgExactLOS,
       ROUND(SUM(CostCents)/100.0,2) AS EstimatedCost,
       ROUND(AVG(CostCents)/100.0,2) AS AvgEstimatedCost
FROM discharge_model
GROUP BY ConditionDescription ORDER BY EstimatedCost DESC;

-- 2. Compare hospitals with sufficient matched data (not a clinical quality ranking).
-- Index 1.0 = observed exact days equal days expected from other NYC hospitals.
SELECT HospitalName, Discharges, MatchedDischarges,
       ROUND(BenchmarkCoverage*100,2) AS CoveragePct,
       ROUND(AvgExactLOS,2) AS AvgExactLOS, ROUND(LOSIndex,3) AS LOSIndex
FROM hospital_summary WHERE MatchedDischarges >= 30
ORDER BY LOSIndex DESC;

-- 3. How much does severity change the LOS distribution?
SELECT ConditionDescription, SeverityKey, Severity, COUNT(*) AS Discharges,
       ROUND(AVG(ExactLOS),2) AS AvgExactLOS,
       ROUND(AVG(CostCents)/100.0,2) AS AvgEstimatedCost
FROM discharge_model GROUP BY ConditionDescription,SeverityKey,Severity
ORDER BY ConditionDescription,SeverityKey;

-- 4. A skew-resistant cost comparison: median via window functions.
WITH ranked AS (
  SELECT ConditionDescription, CostCents,
         ROW_NUMBER() OVER (PARTITION BY ConditionKey ORDER BY CostCents) AS rn,
         COUNT(*) OVER (PARTITION BY ConditionKey) AS n
  FROM discharge_model WHERE CostCents>0
)
SELECT ConditionDescription, ROUND(AVG(CostCents)/100.0,2) AS MedianEstimatedCost
FROM ranked WHERE rn IN ((n+1)/2,(n+2)/2)
GROUP BY ConditionDescription;

-- 5. Discharge destination may explain operational differences; it is not a cause estimate.
SELECT Disposition, COUNT(*) AS Discharges, ROUND(AVG(ExactLOS),2) AS AvgExactLOS
FROM discharge_model GROUP BY Disposition ORDER BY Discharges DESC;

-- 6. Sensitivity: exclude deaths and stays above 30 days, then rebuild peers.
-- Compare movement with the primary index; do not equate a shorter stay with better care.
WITH hs AS (
  SELECT HospitalKey,ConditionKey,SeverityKey,AgeGroup,
         COUNT(*) n,SUM(ExactLOS) days
  FROM clean_discharge WHERE ExactLOS BETWEEN 1 AND 30 AND Disposition!='Expired'
  GROUP BY HospitalKey,ConditionKey,SeverityKey,AgeGroup
), totals AS (
  SELECT ConditionKey,SeverityKey,AgeGroup,SUM(n) n,SUM(days) days,COUNT(*) hospitals
  FROM hs GROUP BY ConditionKey,SeverityKey,AgeGroup
), matched AS (
  SELECT h.*,1.0*(t.days-h.days)/(t.n-h.n) expected
  FROM hs h JOIN totals t USING (ConditionKey,SeverityKey,AgeGroup)
  WHERE t.n-h.n>=30 AND t.hospitals-1>=3
)
SELECT m.HospitalKey, s.HospitalName, SUM(m.n) MatchedDischarges,
       SUM(m.days)/SUM(m.n*m.expected) SensitivityLOSIndex, s.LOSIndex PrimaryLOSIndex
FROM matched m JOIN hospital_summary s USING (HospitalKey)
GROUP BY m.HospitalKey,s.HospitalName,s.LOSIndex HAVING SUM(m.n)>=30
ORDER BY SensitivityLOSIndex DESC;
