# Explain the project in an interview

## A 60-second introduction

“This is an independent portfolio project using public hospital discharge data from New York State. I focused on 89,984 adult discharge records from 52 NYC hospitals across three inpatient clinical groups in 2024. The question was how hospital workload, estimated cost, and length of stay vary, and how to make comparisons less misleading.

The preparation uses Python and SQL to preserve source records, handle capped lengths of stay, and create a star schema. The peer comparison groups records by clinical group, age band, and severity, and excludes each hospital from its own baseline. I checked row counts, joins, costs, and benchmark calculations. The analysis found a strong difference between average and median costs, and substantial LOS differences by severity. The Power BI design makes those definitions and limitations visible.”

Until you have built and tested the report, say **“Power BI design”** or **“Power BI implementation in progress.”** After completion, you can describe the report's actual interactions. Adapt this introduction to work you understand and have personally reviewed.

## Questions you should be able to answer

**Why this dataset?** It is real public administrative data from the official state publisher, with a documented grain and dictionary. The frozen download includes query provenance and a checksum.

**What does one row mean?** One discharge record. It is not one unique patient. The same patient can have multiple hospital stays.

**Why not remove duplicate-looking rows?** De-identification can make separate stays share the same visible values. Ten repeated visible rows had different technical source IDs. There was no evidence supporting their removal.

**What did you clean?** Surrounding whitespace, numeric typing, identifier preservation, cost conversion, and the `120+` sentinel. The raw extract remains unchanged. No selected discharge rows were dropped from the model.

**How did you handle the 120+ values?** Preserve the discharge and cost, set an explicit censoring flag, and leave exact LOS blank. Exact-length averages and peer baselines exclude those records. The distribution still shows them in a separate band.

**Why a star schema?** The discharge fact has one row per record. Hospital, clinical group, severity, age, payer, and LOS-band dimensions supply reusable labels and filters. One-to-many, single-direction relationships reduce ambiguous filtering and make the model easier to reason about.

**Why is there no calendar table?** The public file exposes only discharge year. A daily calendar would add unsupported detail to this single-year project. Monthly or readmission analysis requires another source.

**How does the benchmark work?** For a given hospital, use the mean exact LOS of other hospitals in the same APR DRG, severity, and age band. Require 30 peer records across three other hospitals. Sum assigned expected days over selected matched records and compare with observed days on the same records.

**Why exclude the focal hospital?** Otherwise a hospital's own records pull its reference toward its own performance, especially when it supplies much of a stratum.

**Does LOS Index mean efficiency?** It is a descriptive comparison. Unobserved patient differences, referral patterns, coding, transfers, and discharge support remain. Severity also reflects information from the stay. Shorter LOS is not necessarily better care.

**Why not average the hospital indices for the total?** Ratios have different denominators. The correct total is total matched observed days divided by total matched expected days under the current selection.

**What does a slicer change?** It selects fact records, which changes counts, sums, and weighted comparisons. It does not rebuild the fixed peer pool. County filters still compare selected records with the fixed NYC baseline.

**Why is Scenario disconnected?** It supplies an assumption, not a patient attribute. SELECTEDVALUE reads the selected percentage without filtering discharges through a relationship.

**What does the 5% scenario prove?** Only the arithmetic implication of an assumed reduction. It does not prove feasibility, cash savings, or observed improvement.

**How did you validate?** The downloaded row count matches the API. Source IDs are unique. Dimension keys are unique. Joins preserve row counts. Monetary totals reconcile in integer cents. Every peer stratum is independently checked. Filtered expected values are prepared for the browser report's final verification.

**Did you use AI?** Be candid about the assistance used. Explain what you inspected, reran, corrected, and can independently defend. Do not describe generated work as an entirely unaided build.

## Practice tasks before presenting

1. Run query 1 and explain the difference between total cost and average cost.
2. Find one hospital/condition/severity/age stratum and manually calculate its peer mean using other hospitals.
3. Explain the two different 30-record rules: peer support and display suppression.
4. Show the effect of a condition slicer in your completed report and match it to the check file.
5. Demonstrate the 0%, 5%, and 10% scenario and explain why it is not a savings claim.

## Resume bullet for the completed project

Use only after the Power BI report has been built and validated:

“Built a healthcare analytics portfolio project using 89,984 public hospital discharge records, SQL transformations, a star-schema Power BI model, and DAX measures to explore estimated costs and stratified length-of-stay comparisons across 52 NYC hospitals.”

Do not add a business-improvement percentage unless a real intervention later produces measured evidence.
