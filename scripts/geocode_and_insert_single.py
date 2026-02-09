import sqlite3
import sys
import os
import random
import time
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from address_utils import sanitize_street, geocode_with_fallbacks

def main():
    if len(sys.argv) < 2:
        print('Usage: geocode_and_insert_single.py <web_id>')
        return
    web_id = int(sys.argv[1])
    conn = sqlite3.connect(os.environ.get('BRUETER_DB','brueter.sqlite'))
    cur = conn.cursor()
    cur.execute('SELECT strasse, plz, ort FROM gebaeudebrueter WHERE web_id=?', (web_id,))
    row = cur.fetchone()
    if not row:
        print('No row for', web_id)
        return
    strasse, plz, ort = row
    cleaned, flags, original = sanitize_street(str(strasse))
    # skip if no cleaned street or no house number
    if not cleaned or not __import__('re').search(r"\d", cleaned):
        # mark no_geocode flag
        try:
            cur.execute("UPDATE gebaeudebrueter SET no_geocode=1 WHERE web_id=?", (web_id,))
            conn.commit()
        except Exception:
            pass
        # write report
        try:
            import os, csv
            os.makedirs('reports', exist_ok=True)
            fn = os.path.join('reports', 'no_geocode_marked.csv')
            exists = os.path.exists(fn)
            from datetime import datetime
            with open(fn, 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                if not exists:
                    w.writerow(['web_id','reason','script','timestamp'])
                w.writerow([web_id, 'NO_STREET_OR_NO_NUMBER', 'geocode_and_insert_single', datetime.utcnow().isoformat() + 'Z'])
        except Exception:
            pass
        print('Skipping geocode: no street/number for', web_id)
        conn.close()
        return
    ua = os.environ.get('NOMINATIM_USER_AGENT','Gebaeudebrueter/2026-02')
    locator = Nominatim(scheme='https', user_agent=ua)
    geocode = RateLimiter(locator.geocode, min_delay_seconds=1.0, max_retries=2, error_wait_seconds=2.0)
    time.sleep(random.uniform(0.05,0.25))
    loc, used = geocode_with_fallbacks(lambda a: geocode(a, timeout=10), cleaned, plz or '', ort or 'Berlin')
    if loc:
        lat = str(getattr(loc, 'latitude', None))
        lon = str(getattr(loc, 'longitude', None))
        address = used or ''
        cur.execute(('INSERT OR REPLACE INTO geolocation_osm (web_id, longitude, latitude, location, complete_response) VALUES (?,?,?,?,?)'), (web_id, lon, lat, address, str(loc)))
        conn.commit()
        print('Inserted', web_id, lat, lon)
    else:
        print('No geocode result for', web_id)
    conn.close()

if __name__ == '__main__':
    main()
