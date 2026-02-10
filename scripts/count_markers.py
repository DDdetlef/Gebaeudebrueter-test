import sqlite3

def main():
    conn = sqlite3.connect('brueter.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Try to run the strict query; fall back to a more permissive fetch if schema differs
    try:
        q = ("SELECT b.web_id, o.latitude AS osm_latitude, o.longitude AS osm_longitude, "
             "gg.latitude AS google_latitude, gg.longitude AS google_longitude "
             "FROM gebaeudebrueter b "
             "LEFT JOIN geolocation_osm o ON b.web_id=o.web_id "
             "LEFT JOIN geolocation_google gg ON b.web_id=gg.web_id "
             "WHERE (b.is_test IS NULL OR b.is_test=0) AND (b.noSpecies IS NULL OR b.noSpecies=0)")
        cur.execute(q)
    except sqlite3.OperationalError:
        q = ("SELECT b.web_id, o.latitude AS osm_latitude, o.longitude AS osm_longitude, "
             "gg.latitude AS google_latitude, gg.longitude AS google_longitude "
             "FROM gebaeudebrueter b "
             "LEFT JOIN geolocation_osm o ON b.web_id=o.web_id "
             "LEFT JOIN geolocation_google gg ON b.web_id=gg.web_id "
             "WHERE 1=1")
        cur.execute(q)
    rows = cur.fetchall()
    # Count rows that have usable coordinates (prefer google then osm)
    c = 0
    unique_ids = set()
    for r in rows:
        lat = None
        lon = None
        try:
            if r['google_latitude'] is not None and str(r['google_latitude']) != 'None':
                lat = r['google_latitude']; lon = r['google_longitude']
        except Exception:
            pass
        try:
            if lat is None and r['osm_latitude'] is not None and str(r['osm_latitude']) != 'None':
                lat = r['osm_latitude']; lon = r['osm_longitude']
        except Exception:
            pass
        try:
            if lat is None or lon is None:
                continue
            float(lat); float(lon)
        except Exception:
            continue
        c += 1
        try:
            unique_ids.add(r['web_id'])
        except Exception:
            pass
    print(f"rows_with_coords={c}")
    print(f"unique_web_id_with_coords={len(unique_ids)}")
    conn.close()

if __name__ == '__main__':
    main()
