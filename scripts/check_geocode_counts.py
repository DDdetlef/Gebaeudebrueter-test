import sqlite3
import os
p = os.environ.get('BRUETER_DB', 'brueter.sqlite')
try:
    c = sqlite3.connect(p)
    cur = c.cursor()
    cur.execute('select count(*) from gebaeudebrueter where new=1')
    new = cur.fetchone()[0]
    cur.execute('select count(*) from geolocation_osm')
    osm = cur.fetchone()[0]
    cur.execute('select count(*) from geolocation_google')
    g = cur.fetchone()[0]
    print(f'new={new}, geolocation_osm={osm}, geolocation_google={g}')
    c.close()
except Exception as e:
    print('ERROR', e)
