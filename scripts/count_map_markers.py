import sqlite3
con=sqlite3.connect('brueter.sqlite')
c=con.cursor()
q = ('SELECT gebaeudebrueter.web_id, longitude, latitude from gebaeudebrueter LEFT JOIN geolocation_osm ON gebaeudebrueter.web_id = geolocation_osm.web_id')
rows = c.execute(q).fetchall()
count_possible=0
count_skipped_none=0
count_excluded_1784=0
count_exception=0
for r in rows:
    web_id, longitude, latitude = r
    if web_id==1784:
        count_excluded_1784+=1
        continue
    if latitude=='None' or longitude=='None' or latitude is None or longitude is None:
        count_skipped_none+=1
        continue
    try:
        lat=float(latitude)
        lon=float(longitude)
    except Exception:
        count_exception+=1
        continue
    count_possible+=1
print('total_rows', len(rows))
print('possible markers', count_possible)
print('skipped_none_or_null', count_skipped_none)
print('excluded_1784', count_excluded_1784)
print('parse_exceptions', count_exception)
con.close()
