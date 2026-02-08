import os
import csv
import time
import re
import requests
from geopy.geocoders import Nominatim
from urllib.parse import urlencode
from address_utils import sanitize_street, geocode_with_fallbacks

MISSING_CSV = 'reports/missing_coords.csv'
OUT_CSV = 'reports/geocode_missing_results.csv'
GOOGLE_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_KEY and os.path.exists('api.key'):
    with open('api.key') as f:
        GOOGLE_KEY = f.read().strip()

geolocator = Nominatim(user_agent='gebauedebrueter_geocoder')


# using centralized sanitize_street from address_utils

results = []

with open(MISSING_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

count = 0
google_success = 0
google_fail = 0
osm_success = 0
none = 0

for r in rows:
    web_id = r.get('web_id')
    cleaned, flags, original = sanitize_street(r.get('strasse') or '')
    strasse = cleaned
    plz = (r.get('plz') or '').strip()
    ort = r.get('ort') or 'Berlin'
    # build address
    addr_parts = [strasse, plz, 'Berlin', 'Germany']
    addr = ', '.join([p for p in addr_parts if p])
    found = False
    provider = ''
    lat = ''
    lon = ''
    status = ''

    # If no street provided, skip geocoding entirely
    if not cleaned:
        results.append({'web_id': web_id, 'address': addr, 'provider': 'none', 'lat': '', 'lon': '', 'status': 'NO_STREET'})
        count += 1
        none += 1
        continue

    # Try Google first if key available
    if GOOGLE_KEY:
        params = {'address': addr, 'key': GOOGLE_KEY}
        url = 'https://maps.googleapis.com/maps/api/geocode/json?' + urlencode(params)
        try:
            resp = requests.get(url, timeout=10)
            j = resp.json()
            st = j.get('status')
            if st == 'OK' and j.get('results'):
                loc = j['results'][0]['geometry']['location']
                lat = loc.get('lat')
                lon = loc.get('lng')
                provider = 'google'
                status = 'OK'
                google_success += 1
                found = True
            else:
                status = st
                google_fail += 1
        except Exception as e:
            status = 'error'
            google_fail += 1
        time.sleep(0.1)

    # If not found via Google, try OSM
    if not found:
        # Use geocode_with_fallbacks to try variants against Nominatim
        loc, used = geocode_with_fallbacks(lambda a: geolocator.geocode(a, addressdetails=False, exactly_one=True, timeout=10), cleaned, plz or '', ort or 'Berlin')
        if loc:
            lat = getattr(loc, 'latitude', None)
            lon = getattr(loc, 'longitude', None)
            provider = 'osm'
            status = 'OK'
            osm_success += 1
            found = True
        else:
            status = status or 'ZERO_RESULTS'
            none += 1
        time.sleep(1)

    results.append({'web_id': web_id, 'address': addr, 'provider': provider or 'none', 'lat': lat, 'lon': lon, 'status': status})
    count += 1
    if count % 25 == 0:
        print(f'Processed {count}/{len(rows)}')

# write results
with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['web_id','address','provider','lat','lon','status'])
    w.writeheader()
    for row in results:
        w.writerow(row)

print('Done. Processed', count)
print('google_success=', google_success)
print('google_fail=', google_fail)
print('osm_success=', osm_success)
print('none=', none)
