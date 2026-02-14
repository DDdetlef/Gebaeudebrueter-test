import sqlite3
import csv
import os
import re
from address_utils import sanitize_street

OUT_DIR = 'reports'
OUT_FILE = os.path.join(OUT_DIR, 'geo_report.csv')

def sanitize_street_local(s: str):
    cleaned, flags, original = sanitize_street(s)
    return cleaned

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect('brueter.sqlite')
    cur = conn.cursor()
    cur.execute('SELECT web_id, strasse, strasse_original, plz, ort FROM gebaeudebrueter')
    rows = cur.fetchall()
    total = 0
    missing = 0
    with open(OUT_FILE, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['web_id','adresse_original','adresse_bereinigt','lat','lon','coord_source'])
        writer.writeheader()
        for web_id, strasse, strasse_original, plz, ort in rows:
            total += 1
            orig = (strasse_original or strasse or '')
            cleaned = sanitize_street_local(str(strasse or ''))
            # fetch OSM coords
            cur.execute('SELECT latitude, longitude FROM geolocation_osm WHERE web_id=?', (web_id,))
            osm = cur.fetchone()
            cur.execute('SELECT latitude, longitude FROM geolocation_google WHERE web_id=?', (web_id,))
            goo = cur.fetchone()
            lat = lon = ''
            source = 'none'
            if osm and osm[0] and osm[1]:
                lat, lon = osm[0], osm[1]
                source = 'osm'
            elif goo and goo[0] and goo[1]:
                lat, lon = goo[0], goo[1]
                source = 'google'
            else:
                missing += 1
            writer.writerow({'web_id': web_id, 'adresse_original': orig, 'adresse_bereinigt': cleaned, 'lat': lat, 'lon': lon, 'coord_source': source})
    conn.close()
    print(f'Wrote geo report to {OUT_FILE} — total={total}, missing_coords={missing}')

if __name__ == '__main__':
    main()
