#!/usr/bin/env python3
import csv, sqlite3, shutil
from pathlib import Path

IN = Path('reports') / 'omitted_from_maps_ci.csv'
OUT = Path('reports') / 'omitted_from_maps_ci.csv.tmp'
DB = Path('brueter.sqlite')

if not IN.exists():
    print('Input not found:', IN)
    raise SystemExit(2)

ids = []
with IN.open(encoding='utf-8') as f:
    r = csv.reader(f)
    next(r, None)
    for row in r:
        if row:
            try:
                ids.append(int(row[0]))
            except:
                pass

if not ids:
    print('No ids found in', IN)
    raise SystemExit(0)

con = sqlite3.connect(str(DB))
cur = con.cursor()
cur.execute('PRAGMA table_info(gebaeudebrueter)')
gb_cols = [r[1] for r in cur.fetchall()]
cur.execute('PRAGMA table_info(geolocation_osm)')
osm_cols = [r[1] for r in cur.fetchall()]
cur.execute('PRAGMA table_info(geolocation_google)')
gg_cols = [r[1] for r in cur.fetchall()]

rows = []
for wid in ids:
    cur.execute('SELECT * FROM gebaeudebrueter WHERE web_id=?', (wid,))
    gb_row = cur.fetchone()
    gb_vals = list(gb_row) if gb_row else [None]*len(gb_cols)
    cur.execute('SELECT * FROM geolocation_osm WHERE web_id=?', (wid,))
    osm_row = cur.fetchone()
    osm_vals = list(osm_row) if osm_row else [None]*len(osm_cols)
    cur.execute('SELECT * FROM geolocation_google WHERE web_id=?', (wid,))
    gg_row = cur.fetchone()
    gg_vals = list(gg_row) if gg_row else [None]*len(gg_cols)
    rows.append((wid, gb_vals, osm_vals, gg_vals))

con.close()

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    header = ['web_id'] + [f'gb__{c}' for c in gb_cols] + [f'osm__{c}' for c in osm_cols] + [f'google__{c}' for c in gg_cols]
    w.writerow(header)
    for wid, gb_vals, osm_vals, gg_vals in rows:
        w.writerow([wid] + gb_vals + osm_vals + gg_vals)

shutil.move(str(OUT), str(IN))
print(f'Wrote {len(rows)} records to', IN)
