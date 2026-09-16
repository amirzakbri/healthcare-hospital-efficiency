# New visual upgrades for the three Power BI pages

This guide lists only visuals that were not in the original build. Keep an original visual only where the layout below explicitly says to keep it.

## First add the five optional measures

These measures are not stored in the Excel workbook. Power BI measures live in the semantic model, so create them with **New measure** under Discharges. They are measures 24–28 in `docs/DAX_MEASURES.md`.

The missing Page 2 measure is:

```dax
LOS Variance Days = [Observed Matched Days] - [Expected Matched Days]
```

Format it as `+#,##0.0;-#,##0.0;0.0`. Positive means observed matched bed-days are above the descriptive peer expectation; negative means below.

## Page 1: add one new signature visual

### New: hospital cost Pareto chart

**Question:** How concentrated is selected estimated cost among hospitals?

Add measures 25–27, then insert a **Line and clustered column chart**:

| Field well | Field |
|---|---|
| X-axis | Hospitals.HospitalName |
| Column y-axis | [Estimated Cost] |
| Line y-axis | [Cumulative Cost %] |
| Tooltips | [Discharges], [Avg Estimated Cost], [Hospital Cost Rank] |

Sort HospitalName by **[Estimated Cost], descending**. Format the columns as USD and the line axis from 0% to 100%. Use blue columns and a gold line. Keep every selected hospital so the curve reaches 100%; enable horizontal scrolling or the zoom slider if available.

Replace the original **Estimated cost by clinical group** bar with this Pareto chart. Keep the discharge-by-condition bar, LOS-band distribution, and average-LOS-by-severity chart. Page 1 therefore gains one genuinely new visual without becoming overloaded.

## Page 2: add two new comparison designs

### New: LOS-variance waterfall

**Question:** Which severity groups move total observed days above or below peer expectation?

After creating **[LOS Variance Days]**, insert a **Waterfall chart**:

| Field well | Field |
|---|---|
| Category | Severity.Severity |
| Y-axis | [LOS Variance Days] |
| Tooltips | [Matched Discharges], [Observed Matched Days], [Expected Matched Days] |

Sort severity Minor, Moderate, Major, Extreme. Use blue for negative values, orange for positive values, and charcoal for the total. Keep the zero line and signed labels visible. Title: **Observed minus peer-expected bed-days by severity**.

### New: observed-versus-expected slope small multiples

**Question:** Does the observed-to-expected LOS pattern change across conditions and severity levels?

Insert a **Line chart**:

| Field well | Field |
|---|---|
| X-axis | Severity.Severity |
| Y-axis | [Observed Matched LOS], [Expected Matched LOS] |
| Small multiples | Conditions.Condition |
| Tooltips | [Matched Discharges], [Benchmark Coverage], [LOS Index] |

Use blue with solid markers for observed and gold with a dashed line or open markers for expected. Keep the same Y-axis range across all three panels. Title: **Observed and peer-expected LOS profiles**.

Replace the original clustered-column observed-versus-expected chart with these small multiples. Keep the hospital scatter and matrix. Place the waterfall beside the scatter and the small multiples above the matrix.

## Page 3: replace the two original visuals with three new ones

Page 3 originally used a condition bar and severity matrix. Replace both with the following three visuals. Use `docs/page3_layout_mockup.png` as the placement reference.

### Step 1: create a tiny disconnected bridge table

Choose **New table** and enter:

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

Sort ScenarioBridge.Step by ScenarioBridge.StepSort. Do not create a relationship from this table. Then add measure 28, **[Scenario Bridge Value]**, from `docs/DAX_MEASURES.md`.

If **New table** is unavailable, use **Enter data** to create the same two columns and three rows.

### New: scenario bridge waterfall

**Question:** How does the selected assumption move the matched baseline to the remaining-days scenario?

| Field well | Field |
|---|---|
| Category | ScenarioBridge.Step |
| Y-axis | [Scenario Bridge Value] |
| Tooltips | [Selected Reduction], [Observed Matched Days], [Scenario Bed Days], [Scenario Remaining Days] |

Mark the first and final bars as totals. Use charcoal for totals and orange for the negative reduction. Title: **Matched bed-day scenario bridge**. Subtitle: **Illustrative assumption; not a forecast or measured saving**.

If the web editor does not expose **Set as total**, use Conditions.Condition as Category and [Scenario Bed Days] as Y-axis. Title that fallback **Composition of scenario bed-days by clinical group**.

### New: interactive decomposition tree

**Question:** Where are the scenario bed-days concentrated?

| Field well | Field |
|---|---|
| Analyze | [Scenario Bed Days] |
| Explain by | Conditions.Condition; Severity.Severity; AgeGroups.AgeGroup; Hospitals.HospitalCounty; Hospitals.HospitalName |

Start the visible path with Condition and then Severity. Viewers can expand into age, county, and hospital. Title: **Explore the concentration of scenario bed-days**. Call this concentration, not causal drivers, because the scenario is mechanically proportional to matched observed days.

### New: county-by-severity scenario ribbon chart

**Question:** How does each county's scenario contribution rank change across severity levels?

| Field well | Field |
|---|---|
| X-axis | Severity.Severity |
| Legend | Hospitals.HospitalCounty |
| Y-axis | [Scenario Bed Days] |
| Tooltips | [Matched Discharges], [Observed Matched Days], [Selected Reduction], [Avg Estimated Cost] |

Sort Severity in clinical order and use five restrained category colors. Title: **Scenario bed-day contribution across severity and county**. New York and Kings change rank across the severity levels, which gives the ribbon movement a real analytical purpose. Avoid excessive labels.

### Page 3 layout at 1440 × 900

- Header: page title and scope subtitle.
- Filter strip: Condition, County, Age, Hospital, and the scenario selector.
- KPI strip: Selected Reduction, Observed Matched Days, Scenario Bed Days, Scenario Remaining Days.
- Middle row: scenario bridge at 55% width and decomposition tree at 45%.
- Bottom row: scenario ribbon at about 70% width and the scenario explanation in a 30% text panel.
- Use 10–14 px gaps and align every edge.

## Visual rules across the report

- Blue = observed or primary values; gold = peer expected; orange = scenario change; charcoal = totals and reference lines.
- Keep the new visuals native to Power BI. This avoids custom-visual permission problems and keeps the project easy for recruiters to open.
- Use tooltips for secondary measures instead of adding more cards.
- Give every chart a neutral title and a subtitle stating units or benchmark meaning.
- Test all new visuals with slicers cleared and with one hospital selected. Values must reconcile with the existing cards.
