"""Download a reproducible, bounded cohort from the official SPARCS public API."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATASET = 'sf4k-39ay'
BASE = f'https://health.data.ny.gov/resource/{DATASET}'
WHERE = "health_service_area='New York City' AND apr_drg_code IN ('194','139','720') AND age_group != '0-17'"
FIELDS = [':id AS source_row_id', 'health_service_area', 'hospital_county',
          'permanent_facility_id', 'facility_name', 'age_group', 'length_of_stay',
          'type_of_admission', 'patient_disposition', 'discharge_year',
          'apr_drg_code', 'apr_drg_description', 'apr_severity_of_illness_code',
          'apr_severity_of_illness', 'apr_risk_of_mortality',
          'payment_typology_1', 'emergency_department_indicator',
          'total_charges', 'total_costs']


def fetch(params, fmt='json'):
    url = BASE + '.' + fmt + '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read(), url


def main():
    (ROOT / 'data/raw').mkdir(parents=True, exist_ok=True)
    (ROOT / 'source').mkdir(exist_ok=True)
    metadata_url = f'https://health.data.ny.gov/api/views/{DATASET}.json'
    before = json.load(urllib.request.urlopen(metadata_url, timeout=60))
    count_bytes, count_url = fetch({'$select': 'count(*) AS n', '$where': WHERE})
    count = int(json.loads(count_bytes)[0]['n'])
    rows, urls = [], []
    for offset in range(0, count, 50000):
        raw, url = fetch({'$select': ','.join(FIELDS), '$where': WHERE,
                          '$order': ':id', '$limit': 50000, '$offset': offset}, 'csv')
        page = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        rows.extend(page)
        urls.append(url)
        print(f'Downloaded {len(rows):,} / {count:,} discharge records', flush=True)
    assert len(rows) == count, (len(rows), count)
    assert len({r['source_row_id'] for r in rows}) == count, 'Source row IDs repeat'
    after = json.load(urllib.request.urlopen(metadata_url, timeout=60))
    assert before.get('rowsUpdatedAt') == after.get('rowsUpdatedAt'), 'Source changed during download; rerun'
    path = ROOT / 'data/raw/nyc_adult_selected_discharges_2024.csv'
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        'publisher': 'New York State Department of Health', 'dataset_id': DATASET,
        'dataset_name': before['name'], 'source_url': f'https://health.data.ny.gov/d/{DATASET}',
        'metadata_url': metadata_url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_rows_updated_at': before.get('rowsUpdatedAt'), 'where': WHERE,
        'select': FIELDS, 'count_query_url': count_url, 'download_urls': urls,
        'row_count': count, 'file': str(path.relative_to(ROOT)),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'grain': 'One public de-identified discharge record; not one unique patient',
        'scope': 'Adult age groups; NYC hospital service area; 2024; APR DRG 139, 194, 720',
    }
    (ROOT / 'source/download_manifest.json').write_text(json.dumps(manifest, indent=2))
    (ROOT / 'source/sparcs_2024_metadata.json').write_text(json.dumps(before, indent=2))
    print(json.dumps({'rows': count, 'bytes': path.stat().st_size, 'sha256': manifest['sha256']}))


if __name__ == '__main__':
    main()
