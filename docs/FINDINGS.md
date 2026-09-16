# Findings from the 2024 NYC cohort

These results describe 89,984 adult discharge records from 52 NYC hospitals across three selected APR DRG groups. They do not represent every hospital discharge or every NYC resident. Source: [NYSDOH SPARCS 2024 public-use file](https://health.data.ny.gov/d/sf4k-39ay), downloaded September 4, 2026.

## 1. Septicemia and disseminated infections account for most of the selected activity and cost

| Clinical group | Discharges | Mean exact LOS, days | Mean estimated cost per discharge |
|---|---:|---:|---:|
| Septicemia and disseminated infections | 55,248 | 8.79 | $44,820.39 |
| Heart failure | 25,040 | 6.41 | $30,336.76 |
| Other pneumonia | 9,696 | 5.30 | $24,936.84 |

The septicemia group accounts for 61.4% of selected discharges and 71.2% of estimated costs. This makes it a useful first area for a detailed operational discussion within this project scope. The data do not show that these costs were unnecessary.

**Next question:** For the septicemia group, how do discharge destinations and severity composition differ between hospitals with longer and shorter matched LOS?

Evidence: `analysis/query_01.csv`; query 1 in `sql/02_analysis.sql`.

## 2. Severity changes the comparison substantially

Within heart failure, mean exact LOS rises from 3.32 days in the minor-severity group to 12.47 days in the extreme-severity group. Within the septicemia group, it rises from 3.14 to 12.64 days.

A hospital with more extreme-severity discharges can therefore have a longer raw average without demonstrating inefficient care. The report includes a peer comparison stratified by APR DRG, age band, and severity, and shows both observed and peer-expected LOS.

**Next question:** Does a hospital's observed LOS remain above the descriptive baseline within comparable strata, and how stable is that difference under alternative exclusions?

Evidence: `analysis/query_03.csv`; benchmark construction in `sql/01_transform.sql`.

## 3. Average costs conceal a substantial upper tail

Total estimated cost is $3,477,656,909.17. Mean estimated cost is $38,647.50 per discharge, compared with a median of $23,484.44 when displayed to cents. The exact median is $23,484.435 because it averages the two central values.

The report uses the median alongside aggregate cost. A low-volume, high-cost group should not be evaluated from the mean alone. Large source values are preserved rather than deleted automatically.

**Next question:** Are high-cost stays concentrated in high-severity groups or longer stays, and how much of the pattern remains within the same clinical group?

Evidence: `analysis/summary.json`, `analysis/query_04.csv`.

## 4. Peer coverage is high, but it is not complete risk adjustment

The peer baseline covers 89,877 discharge records, or 99.88% of the cohort. It omits 62 records reported as `120+` days and 45 exact-LOS records without sufficient peer support. A focal hospital is excluded from its own peer pool.

The full-cohort LOS index is approximately 1.00, which is expected for a comparison built from hospitals within the same cohort. It is not evidence that the system is efficient. The meaningful use is filtered exploration with visible sample size, coverage, and clinical context.

The sensitivity analysis removes deaths and stays longer than 30 days and rebuilds the baseline. The largest absolute difference from a hospital's primary index is about 0.130 index points. These changes argue against presenting a definitive league table.

Evidence: `qa/analysis_validation.json`, `analysis/query_06.csv`.

## 5. The scenario quantifies an assumption, not achieved improvement

A 5% reduction applied to the matched baseline of 696,468 observed bed-days produces 34,823.4 hypothetical bed-days. The 0%, 5%, and 10% calculations are included in the Power BI check file.

No intervention, feasibility assessment, marginal-cost model, or observed improvement supports this percentage. Use the page to discuss assumptions, not to claim savings.

## Recommended presentation

Lead with clinical mix and estimated cost. Explain why raw hospital comparisons can mislead. Demonstrate the peer baseline and its exclusions, then show the scenario as a separate assumption-driven exercise. Finish with the next data needed: richer risk factors, discharge-planning information, outcome measures, and staffed-bed data.
