import sqlite3
import csv
import os

DB = 'brueter.sqlite'
OUT = os.path.join('reports', 'has_coords.csv')

def main():
    os.makedirs('reports', exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM gebaeudebrueter')
    total = cur.fetchone()[0]

    # collect good coords from google and osm
    cur.execute("SELECT web_id, latitude, longitude FROM geolocation_google WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    google = cur.fetchall()
    cur.execute("SELECT web_id, latitude, longitude FROM geolocation_osm WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    osm = cur.fetchall()

    google_good = []
    google_bad = []
    for r in google:
        try:
            if r['latitude'] == 'None' or r['longitude'] == 'None':
                raise ValueError
            float(r['latitude']); float(r['longitude'])
            google_good.append((r['web_id'], r['latitude'], r['longitude'], 'google'))
        except Exception:
            google_bad.append((r['web_id'], r['latitude'], r['longitude'], 'google'))

    osm_good = []
    osm_bad = []
    for r in osm:
        try:
            if r['latitude'] == 'None' or r['longitude'] == 'None':
                raise ValueError
            float(r['latitude']); float(r['longitude'])
            osm_good.append((r['web_id'], r['latitude'], r['longitude'], 'osm'))
        except Exception:
            osm_bad.append((r['web_id'], r['latitude'], r['longitude'], 'osm'))

    good_ids = set([int(x[0]) for x in google_good] + [int(x[0]) for x in osm_good])
    bad_parse_ids = set([int(x[0]) for x in google_bad + osm_bad])

    missing_count = total - len(good_ids)

    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['web_id','lat','lon','source'])
        # prefer google when available
        for wid in sorted(good_ids):
            row = next((r for r in google_good if int(r[0])==wid), None)
            if not row:
                row = next((r for r in osm_good if int(r[0])==wid), None)
            if row:
                w.writerow(row)

    print('total=', total)
    print('good_coords_count=', len(good_ids))
    print('missing_count=', missing_count)
    print('bad_parse_count=', len(bad_parse_ids))

    conn.close()


if __name__ == '__main__':
    main()
