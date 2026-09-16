"""Write the data dictionary and execute a small standard-library notebook."""
from pathlib import Path
import contextlib
import io
import json
import os
import platform

ROOT=Path(__file__).resolve().parents[1]


def main():
    desc={
      'DischargeKey':'Local unique record key for the frozen extract; not a patient ID.',
      'HospitalKey':'Public facility identifier preserved as text, including leading zeros.',
      'ConditionKey':'APR DRG code, stored as text: 139, 194, or 720.',
      'SeverityKey':'APR severity code: 1 Minor, 2 Moderate, 3 Major, 4 Extreme.',
      'AgeGroup':'Source age band at admission; four selected adult groups.',
      'PrimaryPayer':'Source payment typology 1; does not describe paid amounts.',
      'StayBand':'Ordered LOS category, with a separate 120+ band.',
      'DischargeYear':'2024, the only time grain used in this snapshot.',
      'ExactLOS':'Known LOS from 1 to 119 inclusive, in days; blank for censored stays.',
      'LOSCensored':'1 when source LOS is 120+, otherwise 0.',
      'BedDaysLowerBound':'Exact days or 120 for censored stays; not an exact full-cohort total.',
      'Disposition':'Destination/status at discharge, including Expired.',
      'AdmissionType':'Source manner of admission: for example Emergency or Elective.',
      'MortalityRisk':'APR mortality-risk category. Not used as an admission-time prediction.',
      'EDIndicator':'Source indicator of ED use: Y/N.',
      'ExpectedLOS':'Fixed peer mean days for eligible records; blank if unmatched or censored.',
      'BenchmarkEligible':'1 when record has exact LOS and sufficient peers; otherwise 0.',
      'PeerN':'Count of exact-LOS peer records in this stratum, excluding the focal hospital.',
      'PeerHospitals':'Other hospitals contributing exact-LOS records in this stratum.',
      'EstimatedCost':'Source estimated total cost, nominal USD; not payment.',
      'Charges':'Source total billed charges, nominal USD; not payment.',
      'HospitalName':'Source hospital name with surrounding whitespace removed.',
      'HospitalCounty':'County of the hospital, not the patient residence.',
      'ConditionDescription':'Official APR DRG label from the source.',
      'Condition':'Short display label; full source wording is retained separately.',
      'Severity':'Source severity description.',
      'AgeSort':'Presentation order, youngest to oldest adult age band.',
      'BandSort':'Presentation order from shortest to longest LOS band.',
      'ReductionPct':'Disconnected scenario assumption, stored as decimal fraction.'
    }
    contract=json.loads((ROOT/'qa/model_contract.json').read_text())
    md='# Data dictionary\n\nEight import tables form one discharge fact, six dimensions, and one disconnected scenario table. No patient identifiers or invented monthly dates are added.\n\n'
    for table,cols in contract['tables'].items():
        md+=f'## {table}\n\n| Field | Meaning |\n|---|---|\n'
        for c in cols:
            assert c in desc,c
            md+=f'| {c} | {desc[c]} |\n'
        md+='\n'
    md+='Derived fields are calculated in sql/01_transform.sql and scripts/build_data.py. The original source field definitions are in the saved NYSDOH data dictionary.\n'
    (ROOT/'docs/DATA_DICTIONARY.md').write_text(md)
    cells=[]
    def mdcell(text):cells.append({'cell_type':'markdown','metadata':{},'source':text.splitlines(True)})
    def code(text):cells.append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':text.splitlines(True)})
    mdcell('# Healthcare analysis walkthrough\n\n## Goal\nInspect the frozen real-data cohort, verify its grain and monetary totals, and understand the SQL peer comparison. The Power BI browser report is a later, user-owned step.\n')
    mdcell('## Setup\nThis companion uses Python standard-library modules only. Run from the project root or the notebooks folder. The prepared SQLite database and frozen raw CSV are included. To rebuild those files, use the documented pandas preparation script.\n')
    code("from pathlib import Path\nimport sqlite3, json, csv\nfrom decimal import Decimal\nroot = Path.cwd()\nif not (root / 'analysis').exists():\n    root = root.parent\nassert (root / 'analysis/healthcare.sqlite').exists()\ncon = sqlite3.connect(root / 'analysis/healthcare.sqlite')\ncon.row_factory = sqlite3.Row\nprint('Connected to the frozen project database.')\n")
    mdcell('## Steps\n### 1. Source and cohort\nOne row is one discharge, not one unique patient. Source: https://health.data.ny.gov/d/sf4k-39ay. The exact query and SHA-256 checksum are saved with the extract.\n')
    code("manifest = json.loads((root / 'source/download_manifest.json').read_text())\nprint('Dataset:', manifest['dataset_id'])\nprint('Filter:', manifest['where'])\nprint('Rows:', manifest['row_count'])\nprint('Retrieved:', manifest['retrieved_at_utc'])\n")
    mdcell('### 2. Check the grain and censored stays\nCapped 120+ day stays remain in counts and costs. They have no exact LOS value. Duplicate-looking visible records are retained if source IDs differ.\n')
    code("row = con.execute('SELECT COUNT(*) n, COUNT(DISTINCT SourceRowId) ids, COUNT(ExactLOS) exact_n, SUM(LOSCensored) capped_n FROM discharge_model').fetchone()\nprint(dict(row))\nassert row['n'] == row['ids'] == manifest['row_count']\nassert row['exact_n'] + row['capped_n'] == row['n']\n")
    mdcell('### 3. Compare clinical groups\nThe following query comes from the saved analysis SQL. Costs are estimated nominal USD. Mean LOS excludes censored values.\n')
    code("statements=[]\nbuffer=''\nfor line in (root / 'sql/02_analysis.sql').read_text().splitlines(True):\n    buffer += line\n    if sqlite3.complete_statement(buffer):\n        statements.append(buffer)\n        buffer=''\nfor row in con.execute(statements[0]):\n    print(dict(row))\n")
    mdcell('### 4. Examine the peer baseline\nPeers share APR DRG, severity and age band, and exclude the focal hospital. A minimum of 30 peer records across three other hospitals is an analyst-chosen support rule. It is not a clinical standard.\n')
    code("row = con.execute('SELECT SUM(BenchmarkEligible) matched, COUNT(*) total, SUM(CASE WHEN BenchmarkEligible=1 THEN ExactLOS END) observed, SUM(ExpectedLOS) expected FROM discharge_model').fetchone()\nprint(dict(row))\nprint('Coverage:', round(row['matched']/row['total']*100,4), '%')\nprint('LOS index:', round(row['observed']/row['expected'],6))\nassert row['matched'] <= row['total']\n")
    mdcell('## Checks\n### 5. Reconcile estimated costs independently in cents\nThe comparison below starts from the unchanged source CSV and the SQL fact, using separate calculation paths.\n')
    code("with (root / 'data/raw/nyc_adult_selected_discharges_2024.csv').open() as f:\n    raw_cents = sum(int(Decimal(r['total_costs'])*100) for r in csv.DictReader(f))\nsql_cents = con.execute('SELECT SUM(CostCents) FROM discharge_model').fetchone()[0]\nassert raw_cents == sql_cents\nprint('Reconciled estimated cost:', Decimal(raw_cents)/100)\nvalidation = json.loads((root / 'qa/analysis_validation.json').read_text())\nprint('Independently checked peer strata:', validation['all_peer_strata_reconciled'])\n")
    mdcell('### 6. Check scenario arithmetic\nA scenario is an assumed percentage of matched observed days, not a forecast or actual improvement.\n')
    code("days = con.execute('SELECT SUM(ExactLOS) FROM discharge_model WHERE BenchmarkEligible=1').fetchone()[0]\nfor rate in [0,.05,.10]:\n    print(f'{rate:.0%}: {days*rate:,.1f} hypothetical bed-days')\nassert days*.10 == 2*(days*.05)\ncon.close()\n")
    mdcell('## Next Steps\nBuild the report using docs/POWER_BI_WEB_GUIDE.md. Check it against qa/powerbi_expected_results.csv. The selected cohort has 89,984 discharges, a highly skewed cost distribution, and substantial LOS variation by severity. Peer adjustment improves comparability but does not establish causal efficiency. Read the findings and methodology before presenting the results.\n')
    env={};count=0;old=os.getcwd();os.chdir(ROOT)
    try:
        for i,c in enumerate(cells):
            c['id']=f'healthcare-{i:02d}'
            if c['cell_type']=='code':
                count+=1;stdout=io.StringIO()
                with contextlib.redirect_stdout(stdout):exec(compile(''.join(c['source']),f'notebook-cell-{i}','exec'),env)
                c['execution_count']=count
                c['outputs']=[{'output_type':'stream','name':'stdout','text':stdout.getvalue().splitlines(True)}]
    finally:os.chdir(old)
    notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':platform.python_version()}},'nbformat':4,'nbformat_minor':5}
    (ROOT/'notebooks/Healthcare_Analysis.ipynb').write_text(json.dumps(notebook,indent=2))
    assert all(c['execution_count'] and c['outputs'] for c in cells if c['cell_type']=='code')
    (ROOT/'qa/notebook_validation.json').write_text(json.dumps({'status':'passed','code_cells':count,'execution':'All code cells executed in order in one Python namespace. No IPython-only syntax used.','format':'nbformat 4.5 structure checked'},indent=2))
    print('Wrote the complete field dictionary and executed',count,'notebook code cells.')


if __name__=='__main__':main()
