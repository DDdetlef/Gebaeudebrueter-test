from geopy.geocoders import Nominatim
from address_utils import sanitize_street
import sqlite3
import os
import time

def main():
    conn = sqlite3.connect('brueter.sqlite')
    cur = conn.cursor()
    cur.execute('SELECT strasse, plz, ort FROM gebaeudebrueter WHERE web_id=?', (2267,))
    row = cur.fetchone()
    if not row:
        print('No row for web_id 2267')
        return
    orig_strasse, plz, ort = row
    cleaned, flags, original = sanitize_street(orig_strasse)
    print('cleaned:', cleaned)
    if cleaned:
        address = f"{cleaned}, {plz}, {ort}, Deutschland"
    else:
        address = f"{plz}, {ort}, Deutschland"
    print('address for geocode:', address)

    ua = os.environ.get('NOMINATIM_USER_AGENT', 'Gebaeudebrueter/2026-02-debug')
    locator = Nominatim(scheme='https', user_agent=ua)
    try:
        loc = locator.geocode(address, timeout=10)
    except Exception as e:
        print('geocode exception:', e)
        loc = None
    print('geocode result:', loc)
    if loc:
        try:
            print('point:', tuple(loc.point))
            print('latitude,longitude:', loc.latitude, loc.longitude)
            print('raw:', loc.raw)
        except Exception as e:
            print('error accessing point:', e)
    conn.close()

if __name__ == '__main__':
    main()
