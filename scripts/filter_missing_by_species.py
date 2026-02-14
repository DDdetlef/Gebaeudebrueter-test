#!/usr/bin/env python3
"""Filter `reports/missing_coords_cleaned.csv` to only rows whose `web_id`
have a species flag set in `reports/scraped_full_export.csv`.

Writes `reports/missing_coords_with_species.csv` with the same columns as the
input missing file but only containing web_ids that have a species flag.
"""
from pathlib import Path
import csv


SCRAPED = Path('reports/scraped_full_export.csv')
MISSING = Path('reports/missing_coords_cleaned.csv')
OUT = Path('reports/missing_coords_with_species.csv')

SPECIES_KEYS = ['mauersegler', 'sperling', 'schwalbe', 'star', 'fledermaus', 'andere']


def load_webids_with_species(scraped_path):
    webids = set()
    if not scraped_path.exists():
        return webids
    with scraped_path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            web = (row.get('web_id') or '').strip()
            if not web:
                continue
            for k in SPECIES_KEYS:
                if row.get(k, '').strip() not in ('', '0'):
                    webids.add(web)
                    break
    return webids


def filter_missing(missing_path, allowed_webids, out_path):
    if not missing_path.exists():
        raise SystemExit(f'Missing input: {missing_path}')
    with missing_path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        rows = [row for row in r if (row.get('web_id') or '').strip() in allowed_webids]
        fieldnames = r.fieldnames or []

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    return len(rows)


def main():
    allowed = load_webids_with_species(SCRAPED)
    kept = filter_missing(MISSING, allowed, OUT)
    print('scraped_has_species_count', len(allowed))
    # count missing input rows
    try:
        with MISSING.open(newline='', encoding='utf-8') as f:
            missing_count = sum(1 for _ in csv.DictReader(f))
    except Exception:
        missing_count = 'n/a'
    print('missing_input_count', missing_count)
    print('kept_for_geocoding', kept)


if __name__ == '__main__':
    main()
