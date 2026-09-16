# Build Hospital Efficiency Explorer in Power BI Desktop

This is the complete Windows Power BI Desktop workflow for rebuilding the project from the beginning. It supersedes the browser instructions for your new build. Do not publish until the local `.pbix` file passes the validation section.

The supplied Excel workbook contains prepared data tables. It does not contain relationships, DAX measures, or finished report pages.

## Files you need

Keep these files together in a stable project folder before connecting Power BI:

- `Healthcare_PowerBI_Data.xlsx`
- `docs/DAX_MEASURES.md`
- `qa/powerbi_expected_results.csv`
- `docs/page3_layout_mockup.png`

Recommended Power BI filename: `Hospital_Efficiency_NYC_2024.pbix`.

## 1. Start the Desktop report

1. Open **Power BI Desktop** and choose **Blank report**.
2. Save immediately as `Hospital_Efficiency_NYC_2024.pbix`.
3. Select **Home > Get data > Excel Workbook**.
4. Select `Healthcare_PowerBI_Data.xlsx`.
5. In Navigator, select these eight named tables:
   - Discharges
   - Hospitals
   - Conditions
   - Severity
   - AgeGroups
   - Payers
   - StayBands
   - Scenario
6. Do not select the worksheet versions of the tables and do not select the Read me sheet.
7. Choose **Transform Data** instead of Load so you can verify the column types first.

Power BI Desktop uses the Navigator to select workbook tables and **Transform Data** opens them in Power Query before loading. [Microsoft: connect to data in Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-quickstart-connect-to-data) and [Microsoft: Power BI Desktop data sources](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-data-sources).

## 2. Check the tables in Power Query

Confirm the queries are named exactly:

`Discharges`, `Hospitals`, `Conditions`, `Severity`, `AgeGroups`, `Payers`, `StayBands`, `Scenario`.

Apply these types:

| Table and columns | Power Query type |
|---|---|
| Discharges.HospitalKey, Hospitals.HospitalKey | Text |
| Discharges.ConditionKey, Conditions.ConditionKey | Text |
| DischargeKey, SeverityKey, DischargeYear | Whole number |
| ExactLOS, LOSCensored, BedDaysLowerBound | Whole number |
| BenchmarkEligible, PeerN, PeerHospitals | Whole number |
| ExpectedLOS | Decimal number |
| EstimatedCost, Charges | Fixed decimal number |
| Scenario.ReductionPct | Decimal number |
| AgeSort, BandSort | Whole number |
| Names, categories, dispositions, and all other descriptive fields | Text |

Check these points before loading:

- Discharges should show **89,984 rows** after loading.
- HospitalKey must remain text. A value such as `001464` must retain its leading zeros.
- ExactLOS and ExpectedLOS contain intentional blanks. Do not replace blanks with zero.
- `120+` remains a valid StayBand category.
- No query should show conversion errors.

Select **Home > Close & Apply**. Wait until all eight tables finish loading.

## 3. Build the star schema

Open **Model view** from the left navigation. Power BI may detect relationships automatically, so inspect every relationship and remove duplicates or incorrect links.

Create these six active relationships through **Modeling > Manage relationships > New**, or drag the matching keys in Model view:

| One side | Many side | Cardinality | Cross-filter direction |
|---|---|---|---|
| Hospitals.HospitalKey | Discharges.HospitalKey | One to many | Single |
| Conditions.ConditionKey | Discharges.ConditionKey | One to many | Single |
| Severity.SeverityKey | Discharges.SeverityKey | One to many | Single |
| AgeGroups.AgeGroup | Discharges.AgeGroup | One to many | Single |
| Payers.PrimaryPayer | Discharges.PrimaryPayer | One to many | Single |
| StayBands.StayBand | Discharges.StayBand | One to many | Single |

The single-direction arrows must point from each dimension table toward Discharges. Keep **Scenario disconnected** with no relationship. Microsoft documents creating and checking cardinality, filter direction, and active relationships in Model view. [Microsoft: create and manage relationships](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-create-and-manage-relationships).

Arrange the model diagram like this:

```text
                  Conditions
                       |
Hospitals ----      Discharges      ---- Severity
                       |
          AgeGroups  Payers  StayBands

Scenario                    ScenarioBridge
(disconnected)              (created later; disconnected)
```

## 4. Set model formatting and sort order

In Data view or Model view, select each label column and use **Column tools > Sort by column**:

- Severity.Severity by Severity.SeverityKey
- AgeGroups.AgeGroup by AgeGroups.AgeSort
- StayBands.StayBand by StayBands.BandSort

Format:

- EstimatedCost and Charges as USD.
- Scenario.ReductionPct as Percentage.
- ExpectedLOS with at least four decimal places in the model; visuals may show fewer.

After the measures are created, hide technical fields from Report view:

- All fact-table keys
- BenchmarkEligible
- PeerN and PeerHospitals
- LOSCensored
- ExpectedLOS
- AgeSort and BandSort

Keep relationship columns in the model. Hiding a field only removes it from the report-building pane.

## 5. Create all 28 measures

Select the Discharges table, then choose **Home > New measure** or right-click Discharges and choose **New measure**. Paste the measures from `docs/DAX_MEASURES.md` one at a time in numbered order.

Measures appear with a calculator icon. Do not use **New column**. Microsoft confirms that a model measure is created under the selected table and recalculates with report filter context. [Microsoft: create measures in Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tutorial-create-measures).

Measures 1–23 provide the core model. Measures 24–28 support the upgraded portfolio visuals:

| Number | Measure | Used for |
|---:|---|---|
| 24 | LOS Variance Days | Page 2 waterfall |
| 25 | Hospital Cost Rank | Page 1 Pareto |
| 26 | Cumulative Estimated Cost | Page 1 Pareto |
| 27 | Cumulative Cost % | Page 1 Pareto |
| 28 | Scenario Bridge Value | Page 3 waterfall |

Use the exact format strings documented in `docs/DAX_MEASURES.md`.

## 6. Create the ScenarioBridge helper table

Select **Modeling > New table** and paste:

```dax
ScenarioBridge =
DATATABLE(
    "Step", STRING,
    "StepSort", INTEGER,
    {
        {"Observed matched days", 1},
        {"Illustrative reduction", 2},
        {"Scenario remaining days", 3}
    }
)
```

Select ScenarioBridge.Step and choose **Column tools > Sort by column > StepSort**. Leave this table disconnected. Then create measure 28, Scenario Bridge Value, if you have not created it already.

## 7. Apply the report design system

For each page, click an empty part of the canvas and open **Format page > Canvas settings**:

- Type: Custom
- Width: 1440 px
- Height: 900 px
- Background: `#F6F8FB`

Microsoft documents custom canvas dimensions, gridlines, snap-to-grid, object locking, and the Selection pane for Power BI Desktop. [Microsoft: report page size and settings](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-report-display-settings).

Use this visual system consistently:

| Role | Color |
|---|---|
| Header and main text | `#18324A` |
| Observed or primary measures | `#2F6B9A` |
| Peer expected | `#C9983A` |
| Scenario change or positive variance | `#DB7C3B` |
| Supporting blue | `#77A9CF` |
| Canvas | `#F6F8FB` |
| Cards and chart backgrounds | `#FFFFFF` |
| Borders and gridlines | `#D8E0E7` |

Use one font family, 14–16 px visual titles, 11–12 px labels, 10–14 px gaps, and consistent alignment. Use **View > Gridlines**, **Snap to grid**, **Selection**, and **Sync slicers** while building.

Create these pages:

1. `01 | Activity & Cost`
2. `02 | Peer Comparison`
3. `03 | Planning Scenario`

## 8. Add and synchronize the main slicers

Create dropdown slicers using:

- Conditions.Condition
- Hospitals.HospitalCounty
- AgeGroups.AgeGroup
- Hospitals.HospitalName

Open **View > Sync slicers**. Synchronize these four slicers across all three pages and make them visible on each page. A synchronized slicer selection affects the selected report pages. [Microsoft: Sync slicers](https://learn.microsoft.com/en-us/power-bi/developer/visuals/enable-sync-slicers).

Page 3 also gets a single-select slicer using Scenario.ReductionPct. Select 5% as the default. Do not synchronize the scenario slicer with Pages 1 and 2.

## 9. Build Page 1: Activity & Cost

Header: **Hospital Efficiency Explorer**

Subtitle: **NYC hospitals | Adult discharge records | 2024 | Three selected APR DRG groups**

Add four cards:

| Card title | Measure |
|---|---|
| Discharge records | [Discharges] |
| Hospitals in selection | [Hospitals] |
| Average LOS under 120 days | [Avg LOS (under 120 days)] |
| Median estimated cost | [Median Estimated Cost] |

Add these visuals:

### Discharges by clinical group

- Visual: Horizontal clustered bar chart
- Y-axis: Conditions.Condition
- X-axis: [Discharges]
- Sort: Descending by Discharges
- Data labels: On

### Discharges by LOS band

- Visual: Clustered column chart
- X-axis: StayBands.StayBand
- Y-axis: [Discharges]
- Sort: StayBand by BandSort
- Axis starts at zero

### Average LOS by severity

- Visual: Clustered column chart
- X-axis: Severity.Severity
- Y-axis: [Avg LOS (under 120 days)]
- Sort: Minor to Extreme
- Axis starts at zero

### Hospital cost Pareto

- Visual: Line and clustered column chart
- X-axis: Hospitals.HospitalName
- Column y-axis: [Estimated Cost]
- Line y-axis: [Cumulative Cost %]
- Tooltips: [Discharges], [Avg Estimated Cost], [Hospital Cost Rank]
- Sort hospitals by [Estimated Cost], descending
- Column axis: USD and starts at zero
- Line axis: 0% to 100%
- Colors: blue columns and gold line
- Enable horizontal scrolling or the zoom slider if available

Layout: KPIs in one row. Use the Pareto chart across about 60% of the main row and the LOS-band chart across 40%. Place the condition bar and severity column chart in the lower row.

Footer: **Estimated costs are not paid amounts. LOS averages exclude 120+ day stays, which remain in discharge and cost totals.**

## 10. Build Page 2: Peer Comparison

Add four cards:

| Card title | Measure |
|---|---|
| Matched discharges | [Matched Discharges] |
| Benchmark coverage | [Benchmark Coverage] |
| Observed matched LOS | [Observed Matched LOS] |
| Expected matched LOS | [Expected Matched LOS] |

Add these visuals:

### Hospital cost and LOS-index bubble chart

- Visual: Scatter chart
- X-axis: [Eligible Avg Cost]
- Y-axis: [LOS Index]
- Values or Details: Hospitals.HospitalName
- Size: [Matched Discharges]
- Legend: Hospitals.HospitalCounty
- Tooltips: [Benchmark Coverage], [Observed Matched LOS], [Expected Matched LOS]
- Add a horizontal constant line at 1.00
- Subtitle: **Bubble size = matched discharges; 1.00 = observed equals peer expected**

If the chart shows one bubble, HospitalName is missing from Values or Details.

### LOS-variance waterfall

- Visual: Waterfall chart
- Category: Severity.Severity
- Y-axis: [LOS Variance Days]
- Tooltips: [Matched Discharges], [Observed Matched Days], [Expected Matched Days]
- Sort: Minor to Extreme
- Positive: orange
- Negative: blue
- Total: charcoal
- Title: **Observed minus peer-expected bed-days by severity**

### Observed-versus-expected LOS small multiples

- Visual: Line chart
- X-axis: Severity.Severity
- Y-axis: [Observed Matched LOS], [Expected Matched LOS]
- Small multiples: Conditions.Condition
- Tooltips: [Matched Discharges], [Benchmark Coverage], [LOS Index]
- Observed: solid blue with markers
- Expected: gold, using a different line or marker style where available
- Keep the same Y-axis range across panels

### Hospital comparison matrix

- Rows: Hospitals.HospitalName
- Values: [Discharges], [Matched Discharges], [Benchmark Coverage], [LOS Index], [Avg Estimated Cost]
- Apply restrained conditional formatting to LOS Index
- Do not average hospital index values for the grand total

Layout: Bubble chart at about 60% width and waterfall at 40%. Place the small multiples above a full-width or wide comparison matrix.

Footer: **Peers are matched on APR DRG, severity, and age. Baselines exclude the focal hospital and remain fixed at NYC scope. This is not a clinical quality ranking.**

## 11. Build Page 3: Planning Scenario

Add the synchronized slicers plus the single-select Scenario.ReductionPct slicer.

Add four cards:

| Card title | Measure |
|---|---|
| Selected reduction | [Selected Reduction] |
| Observed matched days | [Observed Matched Days] |
| Scenario bed-days | [Scenario Bed Days] |
| Scenario remaining days | [Scenario Remaining Days] |

Add these three visuals:

### Matched bed-day scenario bridge

- Visual: Waterfall chart
- Category: ScenarioBridge.Step
- Y-axis: [Scenario Bridge Value]
- Tooltips: [Selected Reduction], [Observed Matched Days], [Scenario Bed Days], [Scenario Remaining Days]
- Mark the first and final bars as totals
- Totals: charcoal
- Reduction step: orange
- Title: **Matched bed-day scenario bridge**
- Subtitle: **Illustrative assumption; not a forecast or measured saving**

### Scenario concentration decomposition tree

- Visual: Decomposition tree
- Analyze: [Scenario Bed Days]
- Explain by, in this order: Conditions.Condition, Severity.Severity, AgeGroups.AgeGroup, Hospitals.HospitalCounty, Hospitals.HospitalName
- Open the initial path through Condition and Severity
- Title: **Explore the concentration of scenario bed-days**

The decomposition tree accepts an aggregate or measure in Analyze and dimensions in Explain By, and users can expand the dimensions in different orders. [Microsoft: decomposition tree visual](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-decomposition-tree).

Describe this as concentration, not causal drivers. Scenario Bed Days is mechanically proportional to matched observed days.

### County-by-severity scenario ribbon

- Visual: Ribbon chart
- X-axis: Severity.Severity
- Legend: Hospitals.HospitalCounty
- Y-axis: [Scenario Bed Days]
- Tooltips: [Matched Discharges], [Observed Matched Days], [Selected Reduction], [Avg Estimated Cost]
- Sort: Minor to Extreme
- Title: **Scenario bed-day contribution across severity and county**

Layout: Copy the structure in `docs/page3_layout_mockup.png`. Place the bridge at 55% width, decomposition tree at 45%, and ribbon across 70% of the bottom row. Use the remaining 30% for this text:

> This scenario multiplies matched observed bed-days by an illustrative reduction percentage. It does not predict a feasible reduction or estimate cash savings. Clinical and discharge-planning review would be needed before setting a target.

Do not label the result as savings achieved, avoidable days, or beds freed.

## 12. Configure interactions

For every page:

1. Select each slicer.
2. Choose **Format > Edit interactions**.
3. Confirm the slicer filters every card and chart on that page.
4. Check chart-to-chart interactions. Use filtering where it improves investigation; use highlighting where viewers need the full comparison context.
5. Make sure selecting a hospital does not produce an all-hospital total in another visual.
6. Clear every selection before saving the default report view.

## 13. Validate the model and visuals

Clear all slicers and cross-highlights. The full cohort must return:

| Measure | Expected result |
|---|---:|
| Discharges | 89,984 |
| Hospitals | 52 |
| Exact LOS Discharges | 89,922 |
| Avg LOS under 120 days | 7.74940504 |
| Median LOS under 120 days | 5 |
| Estimated Cost | $3,477,656,909.17 |
| Median Estimated Cost | $23,484.435 before display rounding |
| Censored Stays | 62 |
| Matched Discharges | 89,877 |
| Benchmark Coverage | 99.88108997% |
| Observed Matched Days | 696,468 |
| Expected Matched Days | 696,827.20868073 |
| LOS Index | 0.99948451 |
| LOS Variance Days | -359.20868073 |
| Scenario Bed Days at 5% | 34,823.4 |
| Scenario Remaining Days at 5% | 661,644.6 |

Use `qa/powerbi_expected_results.csv` to test the provided filtered selections. Also verify:

- 0% produces zero Scenario Bed Days.
- 10% produces 69,646.8 Scenario Bed Days.
- The final point of the unfiltered Pareto curve reaches 100%.
- The scenario bridge shows 696,468, −34,823.4, and 661,644.6 at 5%.
- Every scatter point represents a separate hospital.
- Selecting a single hospital with fewer than 30 matched records leaves LOS Index blank.
- All synchronized slicers affect the intended pages.
- `120+` remains a separate StayBand and is not converted to zero LOS.
- Clearing filters returns all full-cohort values.

## 14. Final Desktop cleanup

1. Rename every visual in the Selection pane with a clear name.
2. Add descriptive Alt text to the main charts.
3. Check spelling, titles, units, decimal places, and long hospital labels.
4. Use **View > Performance Analyzer** and check for unusually slow visuals.
5. Save the PBIX.
6. Close Power BI Desktop, reopen the PBIX, and confirm that all pages, measures, relationships, and default filters remain intact.
7. Save one backup copy before publishing.

## 15. Publishing later

When the report passes review, sign in and select **Home > Publish**, or use **File > Publish > Publish to Power BI**, then select the destination workspace. Publishing sends both the report and its semantic model to the workspace. [Microsoft: publish from Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-upload-desktop-files).

Do not use Publish to web until we review the final report. Publish to web can expose the report and underlying data publicly.

## 16. Send the report for review

Before publishing, send:

- A screenshot of Model view showing all relationships
- A screenshot of each of the three report pages with slicers cleared
- A screenshot of the Page 3 scenario at 5%
- Any DAX or visual error messages
- The final `.pbix` file if you can share it

We will check the numbers, interactions, layout, wording, and portfolio presentation before choosing the publishing method.
