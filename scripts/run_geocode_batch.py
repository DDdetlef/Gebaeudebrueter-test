import csv
import os
import subprocess
import sys

DEFAULT_BATCH = 50
# Prefer the filtered file that contains only web_ids with species when present.
PREFERRED_FILTERED = 'reports/missing_coords_with_species.csv'
SRC_CLEANED = (
    PREFERRED_FILTERED
    if os.path.exists(PREFERRED_FILTERED)
    else ('reports/missing_coords_cleaned.csv' if os.path.exists('reports/missing_coords_cleaned.csv') else 'reports/missing_coords.csv')
)
BATCH_FILE = 'reports/missing_coords_batch.csv'

def make_batch(batch_size=DEFAULT_BATCH, offset=0):
    print('Using source for batch rows:', SRC_CLEANED)
    with open(SRC_CLEANED, encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    subset = rows[offset:offset+batch_size]
    if not subset:
        print('No rows in batch (check offset/batch_size)')
        return False
    with open(BATCH_FILE, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(subset[0].keys()))
        w.writeheader()
        for r in subset:
            w.writerow(r)
    print(f'Wrote batch {len(subset)} rows to {BATCH_FILE}')
    return True

def run_batch(batch_size=DEFAULT_BATCH, offset=0):
    ok = make_batch(batch_size, offset)
    if not ok:
        return
    env = os.environ.copy()
    env['MISSING_CSV'] = os.path.abspath(BATCH_FILE)
    # run geocode_missing.py
    cmd = [sys.executable, 'scripts/geocode_missing.py']
    print('Running:', ' '.join(cmd))
    subprocess.run(cmd, env=env)

if __name__ == '__main__':
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BATCH
    offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    run_batch(batch, offset)
