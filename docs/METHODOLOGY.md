# Scope, definitions, and limitations

## Cohort

The public source is NYSDOH SPARCS inpatient discharges for 2024, dataset `sf4k-39ay`. The query selects `health_service_area = 'New York City'`, APR DRGs `139`, `194`, and `720`, and age groups other than `0-17`. The observed selected age values are `18-29`, `30-49`, `50-69`, and `70 or Older`.

These are discharges from NYC hospitals, not necessarily NYC residents. Records with redacted or missing hospital service area cannot enter this geographic selection. This project does not estimate the size of that omitted NYC population. Clinical groups are APR DRG groupings, not a diagnosis-code search for all possible manifestations of the conditions.

The source contains only discharge year. Admission and discharge month/day are redacted. An artificial calendar or a made-up monthly distribution would be misleading. Some stays may have begun before the discharge year.

## Grain and identifiers

One row represents one discharge record. The API's `:id` is a technical source-row identifier; it is not a patient identifier. `DischargeKey` is a deterministic local row number for this frozen extract. It is not a stable patient or admission ID across source revisions.

Ten rows repeat the other selected visible fields beyond the first occurrence. They have distinct technical source IDs and are retained. Without a true encounter identifier, apparent duplicates after de-identification are not evidence of duplicate discharges.

## Length of stay

The official dictionary defines LOS as discharge date minus admission date plus one, excluding leave-of-absence days. Values of 120 days or longer are represented as `120+`.

| Field or metric | Definition |
|---|---|
| `ExactLOS` | Numeric days for source values 1–119; blank for `120+` |
| `LOSCensored` | 1 for source `120+`, otherwise 0 |
| `BedDaysLowerBound` | Exact days when known; 120 for `120+`. An accounting lower bound, not exact bed-days |
| Average / median LOS | Computed over nonblank `ExactLOS` only |
| LOS distribution | Seven ordered bands, including a separate `120+` band |

The 62 capped stays remain in discharge counts and cost totals. They are excluded from exact-LOS averages and the peer baseline. The default exact-LOS denominator is 89,922, not 89,984. Do not display “average LOS for all stays” as the label.

## Monetary values

`EstimatedCost` is the source's estimated total cost for a discharge. `Charges` is billed charges. Neither represents actual insurer payments, revenue, profit, or marginal avoidable cost. Both are nominal USD. The preparation stage parses source monetary values using decimal arithmetic and reconciles sums in integer cents.

All selected records contain positive numeric cost and charge values. Large values are retained; a high estimated cost alone is not an error. Median estimated cost is also shown to make the skew visible. No inflation adjustment is needed for the single-year scope.

## Peer comparison

For hospital H and a stratum defined by APR DRG × severity × age band:

1. Select records with exact LOS and known severity codes 1–4.
2. Exclude every record from H from that stratum's peer pool.
3. Require at least 30 peer records from at least three other hospitals.
4. Calculate the mean LOS of the remaining peer records.
5. Assign that mean as `ExpectedLOS` to eligible records from H in the stratum.

The SQL uses hospital-level and cohort-level stratum totals to compute these quantities without joining each discharge to every peer discharge.

`LOS Index = SUM(observed exact days on matched records) / SUM(expected days on the same matched records)`.

An index of 1.20 means 20% more observed days than this descriptive peer baseline. It does not establish that 20% of days were avoidable. Index values are blank in the planned DAX measure if the current filtered selection has fewer than 30 matched records. This display rule is separate from the peer-pool rule.

`Benchmark Coverage = matched records / all selected discharge records`. Coverage is 89,877 / 89,984 = 99.8811% for the full cohort. Exclusions are 62 censored stays and 45 exact-LOS records without sufficient peers.

Peer values are frozen at preparation time. Report filters select records and reweight their assigned expected days; they do not recalculate the underlying peer pool. For example, a Queens-only report selection still uses the fixed NYC peer baseline.

## Interpretation limits

This is stratified descriptive benchmarking, not a validated clinical risk model. Within a stratum, hospitals may differ in unobserved illness, referral patterns, transfer status, discharge support, or coding practices. Severity is recorded for the stay and should not be described as a purely admission-time predictor. No confidence intervals, causal effects, or statistically significant outlier labels are claimed.

Deaths and transfers remain in the main analysis. Shorter LOS is not automatically better. A sensitivity analysis rebuilds the peer baseline after excluding deaths and stays longer than 30 days. The observed differences between primary and sensitivity indices support caution about firm rankings; this alternative is also not a clinical quality model.

The extract cannot identify unique patients, calculate linked 30-day readmission rates, determine hospital occupancy, or establish the causes of longer stays. It contains no staffing or staffed-bed denominators.

## Scenario

`Scenario Bed Days = Observed Matched Days × Selected Reduction`.

The scenario table contains 0%, 1%, 2.5%, 5%, 7.5%, 10%, 15%, and 20%. The measure defaults to 5% if no single value is selected. The full-cohort 5% scenario is 34,823.4 bed-days from a matched baseline of 696,468 days.

This is an assumption-driven calculation, not a forecast, clinical target, achieved improvement, or cash-saving estimate. Do not multiply by average cost per day and label the result “savings”: average costs contain fixed components and are not marginal avoidable costs.

## Source documentation

- [SPARCS 2024 dataset](https://health.data.ny.gov/d/sf4k-39ay)
- [NYSDOH public-use access information](https://www.health.ny.gov/statistics/sparcs/access/)
- Official 2024 overview and data dictionary: saved in `source/`; downloadable attachments on the dataset page.
- `source/download_manifest.json` records the exact filter, selected fields, retrieval timestamp, and SHA-256 checksum.
