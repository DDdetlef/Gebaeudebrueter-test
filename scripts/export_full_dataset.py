"""
Export the full `gebaeudebrueter` dataset including flags and geolocation
to a timestamped CSV in `reports/`.

Usage:
  python scripts/export_full_dataset.py --db=brueter.sqlite

Output:
  reports/gebaeudebrueter_YYYYMMDD_HHMMSS.csv
"""
import sqlite3
import os
import sys
from datetime import datetime
import csv

db_path = 'brueter.sqlite'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]

db_path = os.environ.get('BRUETER_DB', db_path)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
out_path = f'reports/gebaeudebrueter_{ts}.csv'
os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# gather columns
geb_cols_info = cur.execute("PRAGMA table_info(gebaeudebrueter)").fetchall()
geb_cols = [c[1] for c in geb_cols_info]

osm_cols = []
google_cols = []
all_tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
if 'geolocation_osm' in all_tables:
    osm_cols_info = cur.execute("PRAGMA table_info(geolocation_osm)").fetchall()
    osm_cols = [c[1] for c in osm_cols_info if c[1] != 'web_id']
if 'geolocation_google' in all_tables:
    google_cols_info = cur.execute("PRAGMA table_info(geolocation_google)").fetchall()
    google_cols = [c[1] for c in google_cols_info if c[1] != 'web_id']

# build select list, prefix geolocation columns
select_cols = [f"geb.{c} AS geb_{c}" for c in geb_cols]
select_cols += [f"osm.{c} AS osm_{c}" for c in osm_cols]
select_cols += [f"gg.{c} AS google_{c}" for c in google_cols]
select_sql = ', '.join(select_cols)

query = f"SELECT {select_sql} FROM gebaeudebrueter geb"
if osm_cols:
    query += " LEFT JOIN geolocation_osm osm ON geb.web_id = osm.web_id"
if google_cols:
    query += " LEFT JOIN geolocation_google gg ON geb.web_id = gg.web_id"

cur.execute(query)
rows = cur.fetchall()

with open(out_path, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.writer(fh)
    # header
    header = [f'geb_{c}' for c in geb_cols] + [f'osm_{c}' for c in osm_cols] + [f'google_{c}' for c in google_cols]
    writer.writerow(header)
    for r in rows:
        writer.writerow([r[h] if h in r.keys() else '' for h in header])

print(f'Wrote {len(rows)} rows to {out_path}')
conn.close()
