import csv
import sqlite3
from pathlib import Path

IN = Path('reports') / 'omitted_from_maps.csv'
OUT = Path('reports') / 'omitted_full.csv'
DB = Path('brueter.sqlite')

def read_omitted(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        return [int(r[0]) for r in reader if r]

def fetch_rows(db_path, ids):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    rows = []
    # get gebaeudebrueter columns
    cur.execute('PRAGMA table_info(gebaeudebrueter)')
    gb_cols = [r[1] for r in cur.fetchall()]
    # get geolocation columns dynamically
    cur.execute('PRAGMA table_info(geolocation_osm)')
    osm_cols = [r[1] for r in cur.fetchall()]
    cur.execute('PRAGMA table_info(geolocation_google)')
    gg_cols = [r[1] for r in cur.fetchall()]

    for wid in ids:
        cur.execute('SELECT * FROM gebaeudebrueter WHERE web_id=?', (wid,))
        gb_row = cur.fetchone()
        gb_dict = {c: gb_row[i] if gb_row else None for i, c in enumerate(gb_cols)}

        cur.execute('SELECT * FROM geolocation_osm WHERE web_id=?', (wid,))
        osm_row = cur.fetchone()
        osm_dict = {c: osm_row[i] if osm_row else None for i, c in enumerate(osm_cols)}

        cur.execute('SELECT * FROM geolocation_google WHERE web_id=?', (wid,))
        gg_row = cur.fetchone()
        gg_dict = {c: gg_row[i] if gg_row else None for i, c in enumerate(gg_cols)}

        rows.append((wid, gb_dict, osm_dict, gg_dict, gb_cols, osm_cols, gg_cols))

    con.close()
    return rows

def write_csv(out_path, rows):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        print('No rows to write')
        return
    _, _, _, _, gb_cols, osm_cols, gg_cols = rows[0]
    header = ['web_id'] + [f'gb__{c}' for c in gb_cols] + [f'osm__{c}' for c in osm_cols] + [f'google__{c}' for c in gg_cols]
    with out_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        for wid, gb_dict, osm_dict, gg_dict, gb_cols, osm_cols, gg_cols in rows:
            gb_vals = [gb_dict.get(c) for c in gb_cols]
            osm_vals = [osm_dict.get(c) for c in osm_cols]
            gg_vals = [gg_dict.get(c) for c in gg_cols]
            w.writerow([wid] + gb_vals + osm_vals + gg_vals)

def main():
    ids = read_omitted(IN)
    if not ids:
        print('No omitted IDs found in', IN)
        return
    rows = fetch_rows(DB, ids)
    write_csv(OUT, rows)
    print(f'Wrote {len(rows)} full records to {OUT}')

if __name__ == '__main__':
    main()
