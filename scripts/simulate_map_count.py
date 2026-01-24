import sqlite3

conn = sqlite3.connect('brueter.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
q=("SELECT b.web_id, o.latitude as osm_latitude, o.longitude as osm_longitude, gg.latitude as google_latitude, gg.longitude as google_longitude "
   "FROM gebaeudebrueter b LEFT JOIN geolocation_osm o ON b.web_id=o.web_id LEFT JOIN geolocation_google gg ON b.web_id=gg.web_id")
cur.execute(q)
rows = cur.fetchall()
count=0
bad_float=[]
missing=0
for r in rows:
    web_id = r['web_id']
    if web_id == 1784:
        continue
    lat=None
    lon=None
    if r['osm_latitude'] is not None and str(r['osm_latitude'])!='None':
        lat=r['osm_latitude']; lon=r['osm_longitude']
    elif r['google_latitude'] is not None and str(r['google_latitude'])!='None':
        lat=r['google_latitude']; lon=r['google_longitude']
    if lat is None or lon is None:
        missing +=1
        continue
    try:
        latf=float(lat); lonf=float(lon)
    except Exception:
        bad_float.append(web_id)
        continue
    count+=1

print('count added:', count)
print('missing:', missing)
print('bad float:', len(bad_float))
if bad_float:
    print('examples bad float:', bad_float[:10])
conn.close()
