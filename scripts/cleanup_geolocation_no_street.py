"""
Delete geolocation rows (OSM and Google) for entries where `gebaeudebrueter.strasse` is empty or NULL.
Run: `python scripts/cleanup_geolocation_no_street.py --db=brueter.sqlite`
"""
import sqlite3
import os
import sys

db_path = 'brueter.sqlite'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]
        break
db_path = os.environ.get('BRUETER_DB', db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Find web_ids where street is NULL or blank (after trimming)
cur.execute("SELECT web_id FROM gebaeudebrueter WHERE strasse IS NULL OR trim(strasse) = ''")
rows = cur.fetchall()
web_ids = [r[0] for r in rows]
print(f'Found {len(web_ids)} entries with empty street.')

if web_ids:
    placeholders = ','.join('?' for _ in web_ids)
    # Count existing geolocation rows to be removed
    cur.execute(f"SELECT COUNT(*) FROM geolocation_osm WHERE web_id IN ({placeholders})", web_ids)
    osm_before = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM geolocation_google WHERE web_id IN ({placeholders})", web_ids)
    google_before = cur.fetchone()[0]

    # Delete
    cur.execute(f"DELETE FROM geolocation_osm WHERE web_id IN ({placeholders})", web_ids)
    cur.execute(f"DELETE FROM geolocation_google WHERE web_id IN ({placeholders})", web_ids)
    conn.commit()

    cur.execute(f"SELECT COUNT(*) FROM geolocation_osm WHERE web_id IN ({placeholders})", web_ids)
    osm_after = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM geolocation_google WHERE web_id IN ({placeholders})", web_ids)
    google_after = cur.fetchone()[0]

    print(f'Removed {osm_before - osm_after} rows from geolocation_osm and {google_before - google_after} rows from geolocation_google.')
else:
    print('No rows to remove.')

conn.close()
