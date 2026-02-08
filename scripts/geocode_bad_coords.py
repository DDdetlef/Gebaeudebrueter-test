import csv
import os
import re
import time
from typing import Optional
import sqlite3
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
import googlemaps

INPUT_CSV = os.environ.get('BAD_COORDS_CSV', 'reports/bad_coords.csv')
OUTPUT_CSV = os.environ.get('BAD_COORDS_OUT', 'reports/geocode_bad_coords_results.csv')
DB_PATH = os.environ.get('BRUETER_DB', 'brueter.sqlite')

GOOGLE_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_KEY and os.path.exists('api.key'):
    try:
        with open('api.key', 'r', encoding='utf-8') as f:
            GOOGLE_KEY = f.read().strip()
    except Exception:
        GOOGLE_KEY = None

ua_base = os.environ.get('NOMINATIM_USER_AGENT') or 'Gebaeudebrueter/2026-02'
ua_url = os.environ.get('NOMINATIM_URL')
ua_email = os.environ.get('NOMINATIM_EMAIL')
ua_extra = []
if ua_email:
    ua_extra.append(ua_email)
if ua_url:
    ua_extra.append(f'+{ua_url}')
UA = ua_base if not ua_extra else f"{ua_base} ({'; '.join(ua_extra)})"

min_delay = float(os.environ.get('GEOCODE_MIN_DELAY_SECONDS', '1.5'))
error_wait = float(os.environ.get('GEOCODE_ERROR_WAIT_SECONDS', '5.0'))
max_retries = int(os.environ.get('GEOCODE_MAX_RETRIES', '3'))

locator = Nominatim(scheme='https', user_agent=UA)
geocode = RateLimiter(locator.geocode, min_delay_seconds=min_delay, max_retries=max_retries, error_wait_seconds=error_wait)

GMAPS: Optional[googlemaps.Client] = None
if GOOGLE_KEY:
    try:
        GMAPS = googlemaps.Client(key=GOOGLE_KEY)
    except Exception:
        GMAPS = None


from address_utils import sanitize_street


def get_address_for_web_id(cur, web_id: int) -> Optional[str]:
    cur.execute('SELECT strasse, plz, ort FROM gebaeudebrueter WHERE web_id=?', (web_id,))
    row = cur.fetchone()
    if not row:
        return None
    strasse, plz, ort = row
    cleaned, flags, original = sanitize_street(str(strasse)) if strasse is not None else ('', {}, '')
    clean_strasse = cleaned
    if clean_strasse:
        return f"{clean_strasse}, {plz or ''}, {ort or 'Berlin'}, Deutschland"
    return f"{plz or ''}, {ort or 'Berlin'}, Deutschland"


def geocode_address(address: str):
    osm_loc = None
    try:
        osm_loc = geocode(address, timeout=10)
    except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable) as e:
        time.sleep(error_wait)
        try:
            osm_loc = geocode(address, timeout=10)
        except Exception:
            osm_loc = None
    lat = str(osm_loc.latitude) if osm_loc else ''
    lon = str(osm_loc.longitude) if osm_loc else ''
    prov = 'osm' if osm_loc else 'none'
    status = 'OK' if osm_loc else 'ZERO_RESULTS'

    if GMAPS and not osm_loc:
        try:
            results = GMAPS.geocode(address)
            if results:
                g_loc = results[0]['geometry']['location']
                lat = str(g_loc.get('lat'))
                lon = str(g_loc.get('lng'))
                prov = 'google'
                status = 'OK'
            else:
                status = 'ZERO_RESULTS'
        except Exception as e:
            status = 'GOOGLE_ERROR'
    return lat, lon, prov, status


def main():
    # open DB connection for address lookup
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # read CSV
    with open(INPUT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    out_rows = []
    total = len(rows)
    for i, r in enumerate(rows, 1):
        web_id = r.get('web_id')
        try:
            web_id_int = int(web_id)
        except Exception:
            web_id_int = None
        if web_id_int is None:
            out_rows.append({'web_id': web_id, 'address': '', 'provider': 'none', 'lat': '', 'lon': '', 'status': 'INVALID_WEB_ID'})
            continue
        address = get_address_for_web_id(cur, web_id_int)
        if not address:
            out_rows.append({'web_id': web_id, 'address': '', 'provider': 'none', 'lat': '', 'lon': '', 'status': 'NO_ADDRESS'})
            continue
        lat, lon, prov, status = geocode_address(address)
        out_rows.append({'web_id': web_id, 'address': address, 'provider': prov, 'lat': lat, 'lon': lon, 'status': status})
        if i % 25 == 0:
            print(f'Processed {i}/{total}')
        time.sleep(0.1)

    # write output
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['web_id','address','provider','lat','lon','status'])
        w.writeheader()
        for row in out_rows:
            w.writerow(row)

    print(f'Done. Processed {len(rows)} rows. Output: {OUTPUT_CSV}')


if __name__ == '__main__':
    main()
