# DAX measures for the browser build

Create each measure under Discharges using New measure, in this order. Copy one code block at a time. These are measure definitions, not calculated columns. DAX execution will be verified in your Power BI account against the supplied expected-results file.

## 1. Discharges

Count of discharge records, not distinct patients.

```dax
Discharges = COUNTROWS(Discharges)
```

Format: `#,##0`. Suggested display folder: Overview.

## 2. Hospitals

Hospitals with discharge records in the selected cohort.

```dax
Hospitals = DISTINCTCOUNT(Discharges[HospitalKey])
```

Format: `#,##0`. Suggested display folder: Overview.

## 3. Exact LOS Discharges

Records with exact LOS between 1 and 119 inclusive.

```dax
Exact LOS Discharges = COUNT(Discharges[ExactLOS])
```

Format: `#,##0`. Suggested display folder: Data quality.

## 4. Avg LOS (under 120 days)

Mean exact LOS; excludes 120+ day stays.

```dax
Avg LOS (under 120 days) = AVERAGE(Discharges[ExactLOS])
```

Format: `0.00`. Suggested display folder: Overview.

## 5. Median LOS (under 120 days)

Median exact LOS; excludes 120+ day stays.

```dax
Median LOS (under 120 days) = MEDIAN(Discharges[ExactLOS])
```

Format: `0.0`. Suggested display folder: Overview.

## 6. Censored Stays

Source reports LOS as 120+; exact duration is unknown.

```dax
Censored Stays = SUM(Discharges[LOSCensored])
```

Format: `#,##0`. Suggested display folder: Data quality.

## 7. Censored Share

Share of selected discharge records with capped LOS.

```dax
Censored Share = DIVIDE([Censored Stays], [Discharges])
```

Format: `0.00%`. Suggested display folder: Data quality.

## 8. Estimated Cost

Sum of estimated costs in nominal 2024 USD; not paid amounts.

```dax
Estimated Cost = SUM(Discharges[EstimatedCost])
```

Format: `$#,##0`. Suggested display folder: Cost.

## 9. Avg Estimated Cost

Mean estimated cost per selected discharge.

```dax
Avg Estimated Cost = AVERAGE(Discharges[EstimatedCost])
```

Format: `$#,##0`. Suggested display folder: Cost.

## 10. Median Estimated Cost

Median estimated cost per selected discharge, including long stays.

```dax
Median Estimated Cost = MEDIAN(Discharges[EstimatedCost])
```

Format: `$#,##0`. Suggested display folder: Cost.

## 11. Charges

Billed charges, distinct from cost and actual payment.

```dax
Charges = SUM(Discharges[Charges])
```

Format: `$#,##0`. Suggested display folder: Cost.

## 12. Matched Discharges

Exact LOS with at least 30 peer records across 3 other hospitals in its stratum.

```dax
Matched Discharges = CALCULATE([Discharges], KEEPFILTERS(Discharges[BenchmarkEligible] = 1))
```

Format: `#,##0`. Suggested display folder: Peer comparison.

## 13. Benchmark Coverage

Matched discharges divided by all selected discharges.

```dax
Benchmark Coverage = DIVIDE([Matched Discharges], [Discharges])
```

Format: `0.00%`. Suggested display folder: Peer comparison.

## 14. Observed Matched Days

Observed bed-days for the matched subset only.

```dax
Observed Matched Days = CALCULATE(SUM(Discharges[ExactLOS]), KEEPFILTERS(Discharges[BenchmarkEligible] = 1))
```

Format: `#,##0`. Suggested display folder: Peer comparison.

## 15. Expected Matched Days

Sum of fixed leave-one-hospital-out peer means for selected matched records.

```dax
Expected Matched Days = SUM(Discharges[ExpectedLOS])
```

Format: `#,##0.0`. Suggested display folder: Peer comparison.

## 16. Observed Matched LOS

Mean observed exact LOS for the matched subset.

```dax
Observed Matched LOS = DIVIDE([Observed Matched Days], [Matched Discharges])
```

Format: `0.00`. Suggested display folder: Peer comparison.

## 17. Expected Matched LOS

Mean peer-expected LOS for the same matched subset.

```dax
Expected Matched LOS = DIVIDE([Expected Matched Days], [Matched Discharges])
```

Format: `0.00`. Suggested display folder: Peer comparison.

## 18. LOS Index

1.0 means observed equals expected. Suppressed below 30 matched records. Descriptive, not a clinical quality score.

```dax
LOS Index = IF([Matched Discharges] >= 30, DIVIDE([Observed Matched Days], [Expected Matched Days]))
```

Format: `0.00"x"`. Suggested display folder: Peer comparison.

## 19. Peer Reference

Reference value for the descriptive LOS index.

```dax
Peer Reference = IF([Matched Discharges] >= 30, 1.0)
```

Format: `0.00"x"`. Suggested display folder: Peer comparison.

## 20. Selected Reduction

Illustrative assumption; defaults to 5% if no single scenario is selected.

```dax
Selected Reduction = SELECTEDVALUE(Scenario[ReductionPct], 0.05)
```

Format: `0.0%`. Suggested display folder: Scenario.

## 21. Scenario Bed Days

Hypothetical reduction in matched observed days; not a forecast or measured saving.

```dax
Scenario Bed Days = [Observed Matched Days] * [Selected Reduction]
```

Format: `#,##0.0`. Suggested display folder: Scenario.

## 22. Scenario Remaining Days

Matched baseline days less illustrative scenario reduction.

```dax
Scenario Remaining Days = [Observed Matched Days] - [Scenario Bed Days]
```

Format: `#,##0.0`. Suggested display folder: Scenario.

## 23. Eligible Avg Cost

Raw average cost; available when at least 30 LOS-matched records exist. Cost itself is not adjusted.

```dax
Eligible Avg Cost = IF([Matched Discharges] >= 30, [Avg Estimated Cost])
```

Format: `$#,##0`. Suggested display folder: Peer comparison.

## 24. LOS Variance Days

Signed difference between observed and peer-expected matched bed-days. Positive means observed days are above the descriptive peer expectation; negative means below.

```dax
LOS Variance Days = [Observed Matched Days] - [Expected Matched Days]
```

Format: `+#,##0.0;-#,##0.0;0.0`. Suggested display folder: Peer comparison.

## 25. Hospital Cost Rank

Dynamic hospital rank by estimated cost inside the current slicer selection.

```dax
Hospital Cost Rank =
RANKX(
    ALLSELECTED(Hospitals[HospitalName]),
    [Estimated Cost],
    ,
    DESC,
    SKIP
)
```

Format: `#,##0`. Suggested display folder: Cost.

## 26. Cumulative Estimated Cost

Running estimated cost across hospitals ranked from highest to lowest cost.

```dax
Cumulative Estimated Cost =
VAR CurrentRank = [Hospital Cost Rank]
VAR RankedHospitals =
    TOPN(
        CurrentRank,
        ALLSELECTED(Hospitals[HospitalName]),
        [Estimated Cost], DESC,
        Hospitals[HospitalName], ASC
    )
RETURN
    SUMX(RankedHospitals, CALCULATE([Estimated Cost]))
```

Format: `$#,##0`. Suggested display folder: Cost.

## 27. Cumulative Cost %

Cumulative share of selected estimated cost used by the hospital Pareto chart.

```dax
Cumulative Cost % =
DIVIDE(
    [Cumulative Estimated Cost],
    CALCULATE([Estimated Cost], ALLSELECTED(Hospitals[HospitalName]))
)
```

Format: `0.0%`. Suggested display folder: Cost.

## 28. Scenario Bridge Value

Create the disconnected `ScenarioBridge` table described in the creative visual guide before adding this measure. It returns the signed values used by the scenario waterfall.

```dax
Scenario Bridge Value =
SWITCH(
    SELECTEDVALUE(ScenarioBridge[Step]),
    "Observed matched days", [Observed Matched Days],
    "Illustrative reduction", -[Scenario Bed Days],
    "Scenario remaining days", [Scenario Remaining Days]
)
```

Format: `#,##0.0`. Suggested display folder: Scenario.
