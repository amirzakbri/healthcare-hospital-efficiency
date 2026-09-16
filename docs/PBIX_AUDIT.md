# Power BI audit and remaining corrections

The PBIX contains a numerically sound model, but several visual, formatting, and refresh issues should be corrected before final Power BI Service publication.

## Verified strengths

- 89,984 unique discharge records.
- Six active many-to-one, single-direction relationships with zero orphan fact keys.
- All 28 intended calculations are present and mathematically correct.
- All 98 expected values across seven filter cases reconcile within numerical tolerance.
- Four shared business slicers are synchronized across all three pages.
- No important visual overlap, clipping, or outside-canvas placement was detected.

## Critical corrections

### 1. Page 1 Average LOS by severity

The chart currently uses `Discharges[SeverityKey]` as the category and `[Discharges]` as the value. It therefore displays discharge counts by numeric severity key while the title claims average LOS.

**Required correction:** Use `Severity[Severity]` on the X-axis and `[Avg LOS (under 120 days)]` on the Y-axis. Sort Minor, Moderate, Major, Extreme.

### 2. Page 3 scenario bridge

The waterfall is sorted by measure value instead of scenario step, and the first and final bars are not stored as totals. This can accumulate the remaining-days value and materially misstate the ending balance.

**Required correction:** Sort `ScenarioBridge[Step]` by `StepSort`, sort the visual by Step ascending, and mark the first and final bars as totals. At the unfiltered 5% scenario, verify 696,468 baseline days, -34,823.4 reduction days, and 661,644.6 remaining days.

## High-priority corrections

1. Replace `[Observed Matched LOS]` with `[Observed Matched Days]` in the Page 3 KPI strip.
2. Use observed and expected matched days in the Page 2 and Page 3 bed-day waterfall tooltips.
3. Configure the scenario slicer for single selection, visibly select 5%, and save Page 1 as the opening page.
4. Configure model sorting: Severity by SeverityKey, AgeGroup by AgeSort, StayBand by BandSort, and ScenarioBridge.Step by StepSort.
5. Sort the LOS-band, severity waterfall, LOS-profile, scenario bridge, and scenario ribbon visuals by their analytical category order.
6. Correct visible formats: Estimated Cost as USD, Cumulative Cost % as a percentage, signed LOS Variance Days without backticks, Peer Reference without backticks, and scenario-day measures to one decimal.
7. Replace the hardcoded `C:\Users\Power BI\Downloads\Healthcare_PowerBI_Data.xlsx` source with a portable parameter or OneDrive/SharePoint connection.
8. Promote the first row in the Payers query; the current dimension contains the invalid value `PrimaryPayer`.
9. Add a 1.00 reference line to the Page 2 hospital scatter.
10. Remove the accidental Page 2 drillthrough configuration that uses `[Discharges]` as a drillthrough field.
11. Add authored alt text, repair tab order, and improve small-text contrast.

## Presentation improvements

- Correct `Audit discharge records` to `Adult discharge records` on Page 1.
- Add page-level headings to Pages 2 and 3.
- Add titles to the Page 2 matrix, Page 2 LOS small multiples, and Page 3 decomposition tree.
- Add a visible Page 3 explanation that the scenario is illustrative rather than a forecast or savings estimate.
- Save the decomposition tree in a neutral root state.
- Add restrained LOS Index conditional formatting to the Page 2 matrix.
- Standardize typography and chart colors.
- Hide technical columns and create measure folders and descriptions.
- Rename `Charges.M` to `Charges`.

The numerical calculations do not require redesign. Correct the visual bindings, scenario state, ordering, formats, and refresh source before presenting the report as final.
