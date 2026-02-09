import sqlite3, json
conn=sqlite3.connect('brueter.sqlite')
conn.row_factory=sqlite3.Row
cur=conn.cursor()
rows=cur.execute('SELECT * FROM gebaeudebrueter WHERE web_id=1784').fetchall()
print('--- gebaeudebrueter ---')
print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
osm=cur.execute('SELECT * FROM geolocation_osm WHERE web_id=1784').fetchall()
print('--- geolocation_osm ---')
print(json.dumps([dict(r) for r in osm], ensure_ascii=False, indent=2))
gg=cur.execute('SELECT * FROM geolocation_google WHERE web_id=1784').fetchall()
print('--- geolocation_google ---')
print(json.dumps([dict(r) for r in gg], ensure_ascii=False, indent=2))
conn.close()
