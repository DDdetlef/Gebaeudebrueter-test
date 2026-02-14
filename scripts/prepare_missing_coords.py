import csv
import os
import sqlite3
import sys
# ensure scripts package path
sys.path.insert(0, os.path.dirname(__file__))
from address_utils import sanitize_street

IN = os.path.join('reports', 'missing_coords.csv')
OUT = os.path.join('reports', 'missing_coords_cleaned.csv')
NO_GEOCODE = os.path.join('reports', 'no_geocode_marked_prepared.csv')

def main():
    os.makedirs('reports', exist_ok=True)
    if not os.path.exists(IN):
        print('Input missing:', IN)
        return

    conn = sqlite3.connect('brueter.sqlite')
    cur = conn.cursor()

    cleaned_rows = []
    no_geo_rows = []

    with open(IN, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            web_id = row.get('web_id')
            strasse = row.get('strasse') or ''
            cleaned, flags, original = sanitize_street(strasse)
            plz = (row.get('plz') or '').strip()
            ort = row.get('ort') or 'Berlin'
            # prepare address for geocoding variants (keep cleaned, plz, ort, flags)
            addr = ', '.join([p for p in [cleaned, plz, ort, 'Deutschland'] if p])
            cleaned_rows.append({'web_id': web_id, 'cleaned': cleaned, 'plz': plz, 'ort': ort, 'address': addr, 'flags': str(flags)})

            # mark records without numeric house number to be skipped by geocoder
            if not cleaned or not any(ch.isdigit() for ch in cleaned):
                try:
                    cur.execute('UPDATE gebaeudebrueter SET no_geocode=1 WHERE web_id=?', (web_id,))
                    conn.commit()
                except Exception:
                    pass
                no_geo_rows.append((web_id, 'NO_STREET_OR_NO_NUMBER'))

    # write cleaned CSV
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['web_id','cleaned','plz','ort','address','flags']
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in cleaned_rows:
            w.writerow(r)

    # write no_geocode marks
    with open(NO_GEOCODE, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['web_id','reason'])
        for r in no_geo_rows:
            w.writerow(r)

    conn.close()
    print('wrote', OUT, 'rows=', len(cleaned_rows))
    print('no_geocode_marked=', len(no_geo_rows), 'written to', NO_GEOCODE)


if __name__ == '__main__':
    main()
