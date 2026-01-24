import sqlite3
con=sqlite3.connect('brueter.sqlite')
c=con.cursor()
q = ('SELECT gebaeudebrueter.web_id, geolocation_osm.longitude, geolocation_osm.latitude '
     'from gebaeudebrueter LEFT JOIN geolocation_osm ON gebaeudebrueter.web_id = geolocation_osm.web_id')
rows = c.execute(q).fetchall()
bad_parse=[]
none_count=0
count_possible=0
count_excluded_1784=0
for web_id, lon, lat in rows:
    if lat is None or lon is None:
        none_count+=1
        continue
    try:
        float(lat); float(lon)
    except Exception:
        bad_parse.append((web_id, lon, lat))
        continue
    if web_id==1784:
        count_excluded_1784+=1
        continue
    count_possible+=1

print('total rows', len(rows))
print('none_count', none_count)
print('bad_parse_count', len(bad_parse))
print('excluded_1784', count_excluded_1784)
print('valid_marker_count', count_possible)
if bad_parse:
    print('samples:', bad_parse[:20])
con.close()
