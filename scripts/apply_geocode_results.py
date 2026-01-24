import sqlite3
import csv
import os

DB = 'brueter.sqlite'
IN_CSV = 'reports/geocode_missing_results.csv'
MISSING_CSV = 'reports/missing_coords.csv'

if not os.path.exists(IN_CSV):
    print('Input CSV not found:', IN_CSV)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()

rows = []
with open(IN_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

applied = 0
applied_osm = 0
applied_google = 0
failed = 0

for r in rows:
    web_id = r.get('web_id')
    provider = (r.get('provider') or '').strip()
    lat = r.get('lat')
    lon = r.get('lon')
    address = r.get('address') or ''
    status = r.get('status') or ''

    if provider in ('osm', 'google') and lat and lon:
        try:
            # ensure floats
            latf = float(lat)
            lonf = float(lon)
        except Exception:
            failed += 1
            continue

        if provider == 'osm':
            cur.execute('INSERT OR REPLACE INTO geolocation_osm(web_id, longitude, latitude, location, complete_response) VALUES (?,?,?,?,?)',
                        (int(web_id), lonf, latf, address, status))
            applied_osm += 1
        else:
            cur.execute('INSERT OR REPLACE INTO geolocation_google(web_id, longitude, latitude, location, complete_response) VALUES (?,?,?,?,?)',
                        (int(web_id), lonf, latf, address, status))
            applied_google += 1
        applied += 1

conn.commit()

# Now update missing_coords.csv to only include rows without provider
remaining = [r for r in rows if (r.get('provider') or '').strip() not in ('osm','google')]

# Attempt to preserve original header if possible by reading original missing file header
if os.path.exists(MISSING_CSV):
    with open(MISSING_CSV, newline='', encoding='utf-8') as f:
        orig = f.readline().strip()
        # try to get header from CSV module
        f.seek(0)
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
else:
    # fallback
    fieldnames = ['web_id','plz','strasse','ort']

with open(MISSING_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in remaining:
        # write only fields present
        out = {k: r.get(k, '') for k in fieldnames}
        w.writerow(out)

print('Applied total:', applied)
print('Applied OSM:', applied_osm)
print('Applied Google:', applied_google)
print('Failed inserts:', failed)
print('Remaining missing entries:', len(remaining))

conn.close()
