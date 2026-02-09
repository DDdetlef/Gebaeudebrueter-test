import sqlite3

conn = sqlite3.connect('brueter.sqlite')
cur = conn.cursor()
q = ("SELECT count(*) FROM gebaeudebrueter b LEFT JOIN geolocation_osm o ON b.web_id=o.web_id LEFT JOIN geolocation_google gg ON b.web_id=gg.web_id WHERE ((o.latitude IS NOT NULL AND o.longitude IS NOT NULL AND o.latitude!='None' AND o.longitude!='None') OR (gg.latitude IS NOT NULL AND gg.longitude IS NOT NULL AND gg.latitude!='None' AND gg.longitude!='None')) AND b.web_id!=1784")
print(cur.execute(q).fetchone()[0])
conn.close()
