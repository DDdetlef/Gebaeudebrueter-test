import sqlite3

con = sqlite3.connect('brueter.sqlite')
cur = con.cursor()
# count total entries in gebaeudebrueter
total = cur.execute('SELECT count(*) FROM gebaeudebrueter').fetchone()[0]
# count rows with osm coords not null and not 'None'
osm_valid = cur.execute("SELECT count(*) FROM geolocation_osm WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude!='None' AND longitude!='None'").fetchone()[0]
# google valid
google_valid = cur.execute("SELECT count(*) FROM geolocation_google WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude!='None' AND longitude!='None'").fetchone()[0]
# either valid for gebaeudebrueter
either = cur.execute("SELECT count(distinct b.web_id) FROM gebaeudebrueter b LEFT JOIN geolocation_osm o ON b.web_id=o.web_id LEFT JOIN geolocation_google g ON b.web_id=g.web_id WHERE (o.latitude IS NOT NULL AND o.longitude IS NOT NULL AND o.latitude!='None' AND o.longitude!='None') OR (g.latitude IS NOT NULL AND g.longitude IS NOT NULL AND g.latitude!='None' AND g.longitude!='None') AND b.web_id!=1784").fetchone()[0]
# count excluded 1784 existence
ex1784 = cur.execute("SELECT count(*) FROM gebaeudebrueter WHERE web_id=1784").fetchone()[0]
# compute none or invalid osm entries joined
joined_osm = cur.execute("SELECT count(*) FROM gebaeudebrueter b LEFT JOIN geolocation_osm o ON b.web_id=o.web_id WHERE o.latitude IS NOT NULL AND o.longitude IS NOT NULL AND o.latitude!='None' AND o.longitude!='None'").fetchone()[0]

print('total gebaeudebrueter=', total)
print('geolocation_osm valid rows=', osm_valid)
print('geolocation_google valid rows=', google_valid)
print('joined_osm_valid=', joined_osm)
print('either_osm_or_google_valid (excluding web_id 1784)=', either)
print('web_id 1784 present in DB=', ex1784)
con.close()
