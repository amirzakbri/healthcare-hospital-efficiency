# Data dictionary

Eight import tables form one discharge fact, six dimensions, and one disconnected scenario table. No patient identifiers or invented monthly dates are added.

## AgeGroups

| Field | Meaning |
|---|---|
| AgeGroup | Source age band at admission; four selected adult groups. |
| AgeSort | Presentation order, youngest to oldest adult age band. |

## Conditions

| Field | Meaning |
|---|---|
| ConditionKey | APR DRG code, stored as text: 139, 194, or 720. |
| ConditionDescription | Official APR DRG label from the source. |
| Condition | Short display label; full source wording is retained separately. |

## Discharges

| Field | Meaning |
|---|---|
| DischargeKey | Local unique record key for the frozen extract; not a patient ID. |
| HospitalKey | Public facility identifier preserved as text, including leading zeros. |
| ConditionKey | APR DRG code, stored as text: 139, 194, or 720. |
| SeverityKey | APR severity code: 1 Minor, 2 Moderate, 3 Major, 4 Extreme. |
| AgeGroup | Source age band at admission; four selected adult groups. |
| PrimaryPayer | Source payment typology 1; does not describe paid amounts. |
| StayBand | Ordered LOS category, with a separate 120+ band. |
| DischargeYear | 2024, the only time grain used in this snapshot. |
| ExactLOS | Known LOS from 1 to 119 inclusive, in days; blank for censored stays. |
| LOSCensored | 1 when source LOS is 120+, otherwise 0. |
| BedDaysLowerBound | Exact days or 120 for censored stays; not an exact full-cohort total. |
| Disposition | Destination/status at discharge, including Expired. |
| AdmissionType | Source manner of admission: for example Emergency or Elective. |
| MortalityRisk | APR mortality-risk category. Not used as an admission-time prediction. |
| EDIndicator | Source indicator of ED use: Y/N. |
| ExpectedLOS | Fixed peer mean days for eligible records; blank if unmatched or censored. |
| BenchmarkEligible | 1 when record has exact LOS and sufficient peers; otherwise 0. |
| PeerN | Count of exact-LOS peer records in this stratum, excluding the focal hospital. |
| PeerHospitals | Other hospitals contributing exact-LOS records in this stratum. |
| EstimatedCost | Source estimated total cost, nominal USD; not payment. |
| Charges | Source total billed charges, nominal USD; not payment. |

## Hospitals

| Field | Meaning |
|---|---|
| HospitalKey | Public facility identifier preserved as text, including leading zeros. |
| HospitalName | Source hospital name with surrounding whitespace removed. |
| HospitalCounty | County of the hospital, not the patient residence. |

## Payers

| Field | Meaning |
|---|---|
| PrimaryPayer | Source payment typology 1; does not describe paid amounts. |

## Scenario

| Field | Meaning |
|---|---|
| ReductionPct | Disconnected scenario assumption, stored as decimal fraction. |

## Severity

| Field | Meaning |
|---|---|
| SeverityKey | APR severity code: 1 Minor, 2 Moderate, 3 Major, 4 Extreme. |
| Severity | Source severity description. |

## StayBands

| Field | Meaning |
|---|---|
| StayBand | Ordered LOS category, with a separate 120+ band. |
| BandSort | Presentation order from shortest to longest LOS band. |

Derived fields are calculated in sql/01_transform.sql and scripts/build_data.py. The original source field definitions are in the saved NYSDOH data dictionary.
