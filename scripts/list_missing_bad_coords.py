import sqlite3
import csv
import os

OUT_DIR = 'reports'
os.makedirs(OUT_DIR, exist_ok=True)

con = sqlite3.connect('brueter.sqlite')
con.row_factory = sqlite3.Row
cur = con.cursor()

# Missing: neither OSM nor Google provides valid lat/lon
missing_q = ("SELECT b.web_id, b.bezirk, b.plz, b.ort, b.strasse, b.update_date "
             "FROM gebaeudebrueter b "
             "LEFT JOIN geolocation_osm o ON b.web_id=o.web_id "
             "LEFT JOIN geolocation_google g ON b.web_id=g.web_id "
             "WHERE NOT (o.latitude IS NOT NULL AND o.longitude IS NOT NULL AND o.latitude!='None' AND o.longitude!='None') "
             "AND NOT (g.latitude IS NOT NULL AND g.longitude IS NOT NULL AND g.latitude!='None' AND g.longitude!='None')")

cur.execute(missing_q)
missing = cur.fetchall()
with open(os.path.join(OUT_DIR,'missing_coords.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['web_id','bezirk','plz','ort','strasse','update_date'])
    for r in missing:
        w.writerow([r['web_id'], r['bezirk'], r['plz'], r['ort'], r['strasse'], r['update_date']])

# Bad parse: lat/lon present but not parseable as float (check both tables)
bad_rows = []
cur.execute("SELECT web_id, latitude, longitude, 'osm' as src FROM geolocation_osm")
for r in cur.fetchall():
    lat = r['latitude']
    lon = r['longitude']
    try:
        if lat is None or lon is None:
            continue
        float(lat); float(lon)
    except Exception:
        bad_rows.append((r['web_id'],'osm', lat, lon))

cur.execute("SELECT web_id, latitude, longitude, 'google' as src FROM geolocation_google")
for r in cur.fetchall():
    lat = r['latitude']
    lon = r['longitude']
    try:
        if lat is None or lon is None:
            continue
        float(lat); float(lon)
    except Exception:
        bad_rows.append((r['web_id'],'google', lat, lon))

with open(os.path.join(OUT_DIR,'bad_coords.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['web_id','source','latitude','longitude'])
    for row in bad_rows:
        w.writerow(row)

print('missing_count=', len(missing))
print('bad_count=', len(bad_rows))
con.close()
