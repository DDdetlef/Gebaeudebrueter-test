import csv
from pathlib import Path

P = Path('reports/omitted_full.csv')
if not P.exists():
    print('missing', P)
    raise SystemExit(1)

issues = []
total = 0
with P.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        total += 1
        wid = row['web_id']
        osm_lat = row.get('osm__latitude')
        osm_lon = row.get('osm__longitude')
        gg_lat = row.get('google__latitude')
        gg_lon = row.get('google__longitude')
        lat = None; lon = None; src = None
        if osm_lat and osm_lat != 'None' and osm_lon and osm_lon != 'None':
            lat = osm_lat; lon = osm_lon; src = 'osm'
        elif gg_lat and gg_lat != 'None' and gg_lon and gg_lon != 'None':
            lat = gg_lat; lon = gg_lon; src = 'google'
        if lat is None:
            issues.append((wid, 'no_coords', osm_lat, osm_lon, gg_lat, gg_lon))
            continue
        try:
            float(lat); float(lon)
        except Exception:
            issues.append((wid, 'non_numeric', osm_lat, osm_lon, gg_lat, gg_lon))

print('processed', total)
print('issues', len(issues))
for i in issues[:50]:
    print(i)
