# Hospital Efficiency Explorer

An end-to-end healthcare analytics portfolio project built with real, public New York State hospital discharge data, SQL, Python, and Power BI.

**Scope:** 89,984 adult discharge records from 52 New York City hospitals in 2024, covering APR DRG 139 (other pneumonia), 194 (heart failure), and 720 (septicemia and disseminated infections).

**Status:** The Power BI Desktop report, prepared import workbook, reproducible data pipeline, analytical outputs, and validation evidence are included. The numerical model reconciles to all 98 expected results across seven validation selections. A final visual-polish and source-portability pass remains before Power BI Service publication; the known items are documented in [`docs/PBIX_AUDIT.md`](docs/PBIX_AUDIT.md).

## Download the dashboard

- [Download the Power BI report](powerbi/Healthcare_Hospital_Efficiency.pbix)
- [Download the prepared Excel import workbook](outputs/healthcare-bi/Healthcare_PowerBI_Data.xlsx)
- [Review the expected Power BI results](qa/powerbi_expected_results.csv)

Power BI Desktop is required to open the PBIX file.

## Business question

Which clinical groups account for hospital workload and estimated cost, and where do observed lengths of stay differ from peers after grouping by condition, severity, and age?

The report supports hospital-operations investigation and portfolio discussion. It does not provide clinical treatment advice or hospital quality rankings.

## Dashboard pages

1. **Activity & Cost** — discharge volume, estimated cost concentration, LOS distribution, clinical group, and severity.
2. **Peer Comparison** — hospital-level LOS index, peer coverage, observed-versus-expected LOS, and signed bed-day variance.
3. **Planning Scenario** — an illustrative reduction assumption applied to matched observed bed-days, with decomposition and contribution views.

## Validated project results

- 89,984 discharge records across 52 NYC hospitals.
- Approximately $3.48 billion in estimated costs; these are not payments or hospital revenue.
- 89,922 records have an exact LOS below 120 days; 62 stays are reported as 120+ and remain censored.
- Mean exact LOS is 7.75 days and median exact LOS is 5 days.
- Median estimated cost is $23,484.44 per discharge; mean cost is $38,647.50.
- The peer comparison covers 89,877 discharges, or 99.88% of the cohort.
- Full-cohort observed matched days are 696,468 versus 696,827.21 peer-expected days.
- The full-cohort LOS Index is 0.99948.
- A 5% illustrative scenario equals 34,823.4 bed-days.

## Analytical method

One record represents one public, de-identified discharge, not one unique patient. The source reports stays of 120 days or longer as `120+`; those records remain in discharge and estimated-cost totals but are excluded from exact LOS averages and peer benchmarks.

The peer benchmark uses the mean exact LOS among other NYC hospitals within the same APR DRG, severity, and age band. The focal hospital is excluded. A stratum requires at least 30 peer records across at least three other hospitals. These are analyst-defined stability thresholds, not clinical standards.

The planning scenario is mechanical:

```text
Scenario Bed Days = Observed Matched Days × Selected Reduction
```

It is not a forecast, a guaranteed capacity gain, a clinical recommendation, or a cash-savings estimate.

See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the complete denominator rules and limitations.

## Data source

Source: [NYSDOH SPARCS 2024 public-use inpatient discharge data](https://health.data.ny.gov/d/sf4k-39ay), retrieved September 4, 2026.

The exact API scope, download URLs, source metadata, row count, and SHA-256 checksum are retained in [`source/download_manifest.json`](source/download_manifest.json). The frozen source extract is included at `data/raw/nyc_adult_selected_discharges_2024.csv` so the published results remain reproducible even if the public source changes later.

## Reproduce the analysis

Python 3.11+ and pandas are sufficient. SQLite is included with Python.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build_data.py
python3 scripts/validate_analysis.py
```

These commands rebuild the local SQLite analysis and star-schema CSV files from the frozen extract, then regenerate and validate the expected Power BI results.

To request a fresh extract from the public API instead of using the frozen snapshot:

```bash
python3 scripts/download_data.py
python3 scripts/build_data.py
python3 scripts/validate_analysis.py
```

A fresh download can change the results. Review the validation outputs before replacing the portfolio snapshot.

## Repository contents

| Path | Purpose |
|---|---|
| `powerbi/` | Power BI Desktop report, DAX definitions, and measure catalog |
| `outputs/healthcare-bi/` | Prepared Excel import workbook |
| `data/raw/` | Frozen public source extract |
| `data/model/` | Eight Power BI-ready star-schema tables |
| `analysis/` | Inspectable analytical query outputs and summary |
| `notebooks/` | Executed analytical walkthrough |
| `sql/` | Transformation, peer benchmark, and analytical queries |
| `scripts/` | Download, preparation, support, and validation scripts |
| `docs/` | Methodology, data dictionary, findings, audit, and presentation guide |
| `qa/` | Data checks, model contract, workbook checks, and expected Power BI results |
| `source/` | Official source documentation, metadata, API scope, and checksum |

## Validation

The project verifies:

- Unique discharge keys and unchanged fact-table grain.
- Unique dimension keys and zero orphan relationships.
- Exact reconciliation of source and modeled costs using integer cents.
- Correct handling of all 62 censored `120+` stays.
- Leave-one-hospital-out peer calculations across every eligible stratum.
- Scenario arithmetic at 0%, 5%, and 10%.
- Seven Power BI filter selections containing 98 expected values.

The embedded PBIX data matches all supplied expected results within numerical tolerance. See [`qa/analysis_validation.json`](qa/analysis_validation.json), [`qa/data_checks.json`](qa/data_checks.json), and [`qa/powerbi_expected_results.csv`](qa/powerbi_expected_results.csv).

## Tools demonstrated

- Power BI Desktop and DAX
- Power Query
- SQL and SQLite
- Python and pandas
- Data modeling and star-schema design
- Data-quality validation and reconciliation
- Healthcare operations analysis
- Analytical documentation and stakeholder communication

## Important limitations

- This is an independent portfolio project, not work performed for a hospital.
- The dataset is public and de-identified, but one row is a discharge rather than a unique patient.
- The analysis is an annual snapshot and cannot support monthly trends.
- The data cannot identify linked readmissions, bed occupancy, or causal effects.
- Estimated costs are not actual payments, reimbursements, or revenue.
- Peer comparisons are descriptive and are not clinical quality ratings.
- Scenario results do not demonstrate achievable savings.

## Portfolio presentation

Use [`docs/INTERVIEW_WALKTHROUGH.md`](docs/INTERVIEW_WALKTHROUGH.md) when preparing to present the project. Discuss the analytical choices, validation evidence, limitations, and remaining dashboard improvements candidly.
