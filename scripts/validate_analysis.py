"""Independent reconciliations and expected Power BI filter outputs."""
from pathlib import Path
from decimal import Decimal
import csv
import json
import sqlite3
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    fact=pd.read_csv(ROOT/'data/model/Discharges.csv',dtype={'HospitalKey':str,'ConditionKey':str})
    hospitals=pd.read_csv(ROOT/'data/model/Hospitals.csv',dtype=str)
    fact=fact.merge(hospitals,on='HospitalKey',how='left',validate='many_to_one')
    expected_count=json.loads((ROOT/'source/download_manifest.json').read_text())['row_count']
    assert len(fact)==expected_count and fact.DischargeKey.is_unique
    assert fact.HospitalName.notna().all()
    summary=json.loads((ROOT/'analysis/summary.json').read_text())
    raw_cost=0
    with (ROOT/'data/raw/nyc_adult_selected_discharges_2024.csv').open() as f:
        for row in csv.DictReader(f):raw_cost+=int(Decimal(row['total_costs'])*100)
    csv_cost=sum(int(Decimal(str(x)).quantize(Decimal('.01'))*100) for x in fact.EstimatedCost)
    assert raw_cost==csv_cost==round(summary['estimated_cost']*100)
    conditions={
      'All cohort':pd.Series(True,index=fact.index),
      'Heart failure only':fact.ConditionKey.eq('194'),
      'Other pneumonia only':fact.ConditionKey.eq('139'),
      'Septicemia group only':fact.ConditionKey.eq('720'),
      'Age 70 or Older':fact.AgeGroup.eq('70 or Older'),
      'Queens hospitals':fact.HospitalCounty.eq('Queens'),
      'Heart failure and age 70 or Older':fact.ConditionKey.eq('194')&fact.AgeGroup.eq('70 or Older')
    }
    results=[]
    for label,mask in conditions.items():
        d=fact[mask];matched=d[d.BenchmarkEligible.eq(1)]
        observed=matched.ExactLOS.sum();expected=matched.ExpectedLOS.sum()
        results.append({'Selection':label,'Discharges':len(d),'Hospitals':d.HospitalKey.nunique(),
          'AvgExactLOS':d.ExactLOS.mean(),'MedianEstimatedCost':d.EstimatedCost.median(),
          'EstimatedCost':round(d.EstimatedCost.sum(),2),'CensoredStays':int(d.LOSCensored.sum()),
          'MatchedDischarges':len(matched),'BenchmarkCoverage':len(matched)/len(d),
          'ObservedMatchedDays':observed,'ExpectedMatchedDays':expected,'LOSIndex':observed/expected,
          'ScenarioBedDays_0pct':0,'ScenarioBedDays_5pct':observed*.05,'ScenarioBedDays_10pct':observed*.1})
    pd.DataFrame(results).to_csv(ROOT/'qa/powerbi_expected_results.csv',index=False,float_format='%.10f')
    with sqlite3.connect(ROOT/'analysis/healthcare.sqlite') as con:
        n,cost=con.execute('SELECT COUNT(*),SUM(CostCents) FROM discharge_model').fetchone()
        assert n==len(fact) and cost==raw_cost
        sql_distribution=pd.read_sql_query('SELECT StayBand,COUNT(*) n FROM discharge_model GROUP BY StayBand',con).set_index('StayBand')['n']
        assert fact.groupby('StayBand').size().sort_index().equals(sql_distribution.sort_index())
        sql_condition=pd.read_sql_query('SELECT ConditionKey,COUNT(*) n FROM discharge_model GROUP BY ConditionKey',con).set_index('ConditionKey')['n']
        assert fact.groupby('ConditionKey').size().sort_index().equals(sql_condition.sort_index())
        # Validate EVERY hospital/stratum against independent pandas group aggregates.
        hs=pd.read_sql_query('SELECT * FROM benchmark',con)
        exact=fact[fact.ExactLOS.notna()]
        groups=['ConditionKey','SeverityKey','AgeGroup']
        pool=exact.groupby(groups).agg(n=('DischargeKey','size'),days=('ExactLOS','sum'),hospitals=('HospitalKey','nunique'))
        focal=exact.groupby(['HospitalKey']+groups).agg(n=('DischargeKey','size'),days=('ExactLOS','sum'))
        for row in hs.itertuples(index=False):
            key=(row.ConditionKey,row.SeverityKey,row.AgeGroup)
            all_=pool.loc[key];own=focal.loc[(row.HospitalKey,)+key]
            peer_n=int(all_['n']-own['n']);peer_h=int(all_['hospitals']-1)
            assert row.PeerN==peer_n and row.PeerHospitals==peer_h
            if peer_n>=30 and peer_h>=3:assert abs(row.ExpectedLOS-(all_['days']-own['days'])/peer_n)<1e-10
            else:assert pd.isna(row.ExpectedLOS)
    out={'status':'passed','row_count':len(fact),'cost_cents':raw_cost,
         'all_peer_strata_reconciled':len(hs),'filter_test_cases':len(results),
         'checks':['raw-to-CSV-to-SQL row and cost totals','dimension join cardinality',
                   'complete condition and stay-band reconciliation','all leave-one-hospital-out strata',
                   'scenario arithmetic for 0%, 5%, 10%'],
         'not_executed':'DAX evaluation and report interaction testing in the user Power BI service account'}
    (ROOT/'qa/analysis_validation.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
