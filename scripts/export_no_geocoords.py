import sqlite3
import csv
import os

OUT_DIR = 'reports'
OUT_FILE = os.path.join(OUT_DIR, 'no_geocoords.csv')

def is_missing(val):
    if val is None:
        return True
    s = str(val).strip()
    if s == '' or s.lower() == 'none':
        return True
    return False

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect('brueter.sqlite')
    cur = conn.cursor()
    q = ('SELECT g.web_id, g.strasse, g.plz, g.ort, g.strasse_original, '
         'o.longitude, o.latitude, o.location, gr.longitude as g_long, gr.latitude as g_lat '
         'FROM gebaeudebrueter g '
         'LEFT JOIN geolocation_osm o ON o.web_id = g.web_id '
         'LEFT JOIN geolocation_google gr ON gr.web_id = g.web_id')
    cur.execute(q)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    out_rows = []
    for r in rows:
        # r: web_id, strasse, plz, ort, strasse_original, o.lon, o.lat, o.location, g_long, g_lat
        web_id = r[0]
        o_lon = r[5]
        o_lat = r[6]
        g_lon = r[8]
        g_lat = r[9]
        osm_missing = is_missing(o_lon) or is_missing(o_lat)
        google_missing = is_missing(g_lon) or is_missing(g_lat)
        if osm_missing and google_missing:
            out_rows.append({
                'web_id': web_id,
                'strasse': r[1],
                'plz': r[2],
                'ort': r[3],
                'strasse_original': r[4],
                'osm_longitude': o_lon,
                'osm_latitude': o_lat,
                'osm_location': r[7],
                'google_longitude': g_lon,
                'google_latitude': g_lat,
            })

    with open(OUT_FILE, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['web_id','strasse','plz','ort','strasse_original','osm_longitude','osm_latitude','osm_location','google_longitude','google_latitude'])
        writer.writeheader()
        for row in out_rows:
            writer.writerow(row)

    conn.close()
    print(f'Wrote {len(out_rows)} rows to {OUT_FILE}')

if __name__ == '__main__':
    main()
