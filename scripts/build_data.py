"""Build the SQLite analysis and Power BI star-schema CSVs from the frozen source."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    for folder in ['data/model','analysis','qa','docs','notebooks','powerbi']:
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    manifest = json.loads((ROOT/'source/download_manifest.json').read_text())
    rawpath = ROOT/manifest['file']
    assert hashlib.sha256(rawpath.read_bytes()).hexdigest()==manifest['sha256']
    raw = pd.read_csv(rawpath,dtype=str,keep_default_na=False)
    raw = raw.apply(lambda column: column.str.strip())
    assert len(raw)==manifest['row_count'] and raw.source_row_id.is_unique
    visible_duplicates = int(raw.drop(columns='source_row_id').duplicated().sum())
    missing = {c:int(raw[c].eq('').sum()) for c in raw.columns}
    assert set(raw.age_group)<= {'18-29','30-49','50-69','70 or Older'}
    assert set(raw.discharge_year)=={'2024'}
    assert set(raw.apr_drg_code)=={'139','194','720'}
    assert set(raw.health_service_area)=={'New York City'}
    assert raw.length_of_stay.map(lambda x: x=='120+' or (x.isdigit() and 1<=int(x)<=119)).all()
    for source,target in [('total_costs','CostCentsParsed'),('total_charges','ChargesCentsParsed')]:
        raw[target] = raw[source].map(lambda x: int(Decimal(x)*100))
        assert raw[target].gt(0).all()
    dbpath=ROOT/'analysis/healthcare.sqlite'
    with sqlite3.connect(dbpath) as con:
        raw.to_sql('raw_discharge',con,if_exists='replace',index=False)
        con.executescript((ROOT/'sql/01_transform.sql').read_text())
        model=pd.read_sql_query('SELECT * FROM discharge_model ORDER BY DischargeKey',con)
        hospital=pd.read_sql_query('SELECT * FROM hospital_summary ORDER BY Discharges DESC',con)
        assert len(model)==len(raw) and model.DischargeKey.is_unique
        assert int(model.CostCents.sum())==int(raw.CostCentsParsed.sum())
        assert model.loc[model.LOSCensored.eq(1),'ExactLOS'].isna().all()
        assert model.loc[model.BenchmarkEligible.eq(1),'PeerN'].ge(30).all()
        assert model.loc[model.BenchmarkEligible.eq(1),'PeerHospitals'].ge(3).all()
        assert abs(hospital.TotalEstimatedCost.sum()-model.CostCents.sum()/100)<.01
        # Independent check: direct peer rows exclude the focal hospital.
        eligible=model[model.BenchmarkEligible.eq(1)]
        strata=eligible[['HospitalKey','ConditionKey','SeverityKey','AgeGroup']].drop_duplicates()
        for row in strata.iloc[::max(1,len(strata)//25)].itertuples(index=False):
            peer=model[(model.HospitalKey!=row.HospitalKey)&(model.ConditionKey==row.ConditionKey)&
                       (model.SeverityKey==row.SeverityKey)&(model.AgeGroup==row.AgeGroup)&model.ExactLOS.notna()]
            actual=eligible[(eligible.HospitalKey==row.HospitalKey)&(eligible.ConditionKey==row.ConditionKey)&
                            (eligible.SeverityKey==row.SeverityKey)&(eligible.AgeGroup==row.AgeGroup)].ExpectedLOS.iloc[0]
            assert abs(peer.ExactLOS.mean()-actual)<1e-10
        # SQL comments can contain semicolons; use sqlite's complete_statement parser.
        statements=[];buf=''
        for line in (ROOT/'sql/02_analysis.sql').read_text().splitlines(True):
            buf+=line
            if sqlite3.complete_statement(buf):statements.append(buf);buf=''
        for i,query in enumerate(statements,1):
            pd.read_sql_query(query,con).to_csv(ROOT/f'analysis/query_{i:02d}.csv',index=False)
    hospital.to_csv(ROOT/'analysis/hospital_summary.csv',index=False)

    condition_names={'139':'Other pneumonia','194':'Heart failure','720':'Septicemia / disseminated infections'}
    dims={
      'Hospitals':model[['HospitalKey','HospitalName','HospitalCounty']].drop_duplicates().sort_values('HospitalKey'),
      'Conditions':model[['ConditionKey','ConditionDescription']].drop_duplicates().sort_values('ConditionKey'),
      'Severity':model[['SeverityKey','Severity']].drop_duplicates().sort_values('SeverityKey'),
      'AgeGroups':pd.DataFrame({'AgeGroup':['18-29','30-49','50-69','70 or Older'],'AgeSort':[1,2,3,4]}),
      'Payers':model[['PrimaryPayer']].drop_duplicates().sort_values('PrimaryPayer'),
      'StayBands':pd.DataFrame({'StayBand':['1-2 days','3-5 days','6-10 days','11-20 days','21-30 days','31-119 days','120+ days'], 'BandSort':list(range(1,8))}),
      'Scenario':pd.DataFrame({'ReductionPct':[0,.01,.025,.05,.075,.1,.15,.2]})
    }
    dims['Conditions']['Condition']=dims['Conditions'].ConditionKey.map(condition_names)
    factcols=['DischargeKey','HospitalKey','ConditionKey','SeverityKey','AgeGroup','PrimaryPayer',
              'StayBand','DischargeYear','ExactLOS','LOSCensored','BedDaysLowerBound','Disposition',
              'AdmissionType','MortalityRisk','EDIndicator','ExpectedLOS','BenchmarkEligible','PeerN','PeerHospitals']
    fact=model[factcols].copy()
    fact['EstimatedCost']=model.CostCents/100
    fact['Charges']=model.ChargesCents/100
    for key in ['HospitalKey','ConditionKey','SeverityKey','AgeGroup','PrimaryPayer','StayBand']:
        dim=next(v for k,v in dims.items() if key in v.columns)
        assert dim[key].is_unique, key
        assert fact[key].isin(dim[key]).all(), key
    for name,frame in {'Discharges':fact,**dims}.items():
        if name=='Discharges':
            frame=frame.copy()
            for currency in ['EstimatedCost','Charges']:
                frame[currency]=frame[currency].map(lambda value: f'{value:.2f}')
        frame.to_csv(ROOT/f'data/model/{name}.csv',index=False,float_format='%.10f')
    model[['HospitalName','ConditionDescription','Severity','AgeGroup','ExactLOS','LOSCensored','CostCents']].head(5).to_csv(ROOT/'analysis/source_preview.csv',index=False)
    checks={
      'status':'passed','source_count':len(raw),'model_count':len(fact),
      'hospital_count':len(dims['Hospitals']),'missing_source_fields':missing,
      'duplicate_source_ids':int(raw.source_row_id.duplicated().sum()),
      'repeated_visible_rows_retained':visible_duplicates,
      'censored_los_count':int(model.LOSCensored.sum()),
      'exact_los_count':int(model.ExactLOS.notna().sum()),
      'benchmark_eligible':int(model.BenchmarkEligible.sum()),
      'benchmark_coverage':float(model.BenchmarkEligible.mean()),
      'total_estimated_cost_cents':int(model.CostCents.sum()),
      'sum_cost_reconciliation':'exact in integer cents',
      'joins':'dimension keys unique; zero orphans; fact row count unchanged',
      'peer_check':'independent direct-row calculation agrees for systematic stratum sample',
      'power_bi_engine_validation':'User will build the report in Power BI service; DAX execution and report rendering are pending that step.'
    }
    (ROOT/'qa/data_checks.json').write_text(json.dumps(checks,indent=2))
    summary={
      'discharges':len(model),'hospitals':len(dims['Hospitals']),
      'avg_exact_los':float(model.ExactLOS.mean()),'median_exact_los':float(model.ExactLOS.median()),
      'estimated_cost':int(model.CostCents.sum())/100,
      'avg_estimated_cost':float(model.CostCents.mean()/100),
      'median_estimated_cost':float(model.CostCents.median()/100),
      'censored_los_count':int(model.LOSCensored.sum()),
      'benchmark_eligible':int(model.BenchmarkEligible.sum()),
      'benchmark_coverage':float(model.BenchmarkEligible.mean()),
      'matched_observed_days':int(eligible.ExactLOS.sum()),
      'matched_expected_days':float(eligible.ExpectedLOS.sum()),
      'los_index':float(eligible.ExactLOS.sum()/eligible.ExpectedLOS.sum()),
      'five_percent_scenario_bed_days':float(eligible.ExactLOS.sum()*.05),
      'raw_preview':model[['HospitalName','ConditionDescription','ExactLOS']].head(3).to_dict('records')
    }
    (ROOT/'analysis/summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
