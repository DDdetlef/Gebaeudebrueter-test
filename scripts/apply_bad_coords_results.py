import sqlite3
import csv
import os

DB = os.environ.get('BRUETER_DB', 'brueter.sqlite')
IN_CSV = os.environ.get('BAD_COORDS_OUT', 'reports/geocode_bad_coords_results.csv')

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
            latf = float(lat)
            lonf = float(lon)
            web_id_int = int(web_id)
        except Exception:
            failed += 1
            continue

        if provider == 'osm':
            cur.execute('INSERT OR REPLACE INTO geolocation_osm(web_id, longitude, latitude, location, complete_response) VALUES (?,?,?,?,?)',
                        (web_id_int, lonf, latf, address, status))
            applied_osm += 1
        else:
            cur.execute('INSERT OR REPLACE INTO geolocation_google(web_id, longitude, latitude, location, complete_response) VALUES (?,?,?,?,?)',
                        (web_id_int, lonf, latf, address, status))
            applied_google += 1
        applied += 1

conn.commit()

print('Applied total:', applied)
print('Applied OSM:', applied_osm)
print('Applied Google:', applied_google)
print('Failed inserts:', failed)

conn.close()
