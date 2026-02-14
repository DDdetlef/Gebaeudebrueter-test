from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
import sqlite3
import googlemaps
import time
import os
import re
import sys
import random
from address_utils import sanitize_street, geocode_with_fallbacks

db_path = 'brueter.sqlite'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=', 1)[1]
        break
db_path = os.environ.get('BRUETER_DB', db_path)
try:
    sqliteConnection = sqlite3.connect(db_path)
    cursor = sqliteConnection.cursor()
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)

key = os.environ.get('GOOGLE_API_KEY')
if not key:
    try:
        with open('api.key', 'r') as file:
            key = file.read().strip()
    except Exception:
        key = None

gmaps = None
if key:
    try:
        gmaps = googlemaps.Client(key=key)
    except Exception as e:
        print(f"WARN: Google client init failed: {e}. Proceeding without Google geocoding.")
else:
    print('WARN: No Google API key found. Proceeding with OSM-only geocoding.')

cursor.execute('SELECT web_id, strasse, ort, plz, beschreibung from gebaeudebrueter where new=1')
data = cursor.fetchall()
# only updates new entries which are set to new=1

# Use a clear, identifiable user agent per Nominatim policy.
# Include a way to contact or a project URL.
ua_base = os.environ.get('NOMINATIM_USER_AGENT')
ua_url = os.environ.get('NOMINATIM_URL')
ua_email = os.environ.get('NOMINATIM_EMAIL')
if not ua_base:
    ua_base = 'Gebaeudebrueter/2026-02'
ua_extra = []
if ua_email:
    ua_extra.append(ua_email)
if ua_url:
    # prepend + per convention for URLs in UA
    ua_extra.append(f'+{ua_url}')
ua = ua_base if not ua_extra else f"{ua_base} ({'; '.join(ua_extra)})"
locator = Nominatim(
    scheme='https',
    user_agent=ua,
)
# Be conservative with rate limiting to avoid overload denial.
# Add retries and a wait between retries.
min_delay = float(os.environ.get('GEOCODE_MIN_DELAY_SECONDS', '1.5'))
error_wait = float(os.environ.get('GEOCODE_ERROR_WAIT_SECONDS', '5.0'))
max_retries = int(os.environ.get('GEOCODE_MAX_RETRIES', '3'))
geocode = RateLimiter(
    locator.geocode,
    min_delay_seconds=min_delay,
    max_retries=max_retries,
    error_wait_seconds=error_wait,
)

index = 0
# Optional limit to process a smaller batch per run: --limit=N
limit = None
for arg in sys.argv[1:]:
    if arg.startswith("--limit="):
        try:
            limit = int(arg.split("=", 1)[1])
        except Exception:
            pass
for (web_id, strasse, ort, plz, beschreibung) in data:
    if limit is not None and index >= limit:
        break
    clean_strasse, flags, original_strasse = sanitize_street(str(strasse))
    # If no street present after cleaning, skip geocoding (do not geocode by PLZ only)
    location = None
    if clean_strasse:
        # Try geocoding with fallback variants using the RateLimiter-wrapped geocode callable
        time.sleep(random.uniform(0.05, 0.25))
        try:
            location, used_addr = geocode_with_fallbacks(lambda a: geocode(a, timeout=10), clean_strasse, plz or '', ort or 'Berlin', max_attempts=max_retries, pause=min_delay)
        except Exception as e:
            print(f"OSM geocode error for {web_id}: {e}.")
            location = None
    else:
        print(f"Skipping geocode for web_id {web_id}: no street provided")
    if location:
        point = tuple(location.point)
        latitude = str(point[0])
        longitude = str(point[1])
        query = ('INSERT OR REPLACE INTO geolocation_osm'
                 '(web_id, longitude, latitude, location, complete_response)'
                 'VALUES (?,?,?,?,?)')
        value = (web_id, longitude, latitude, str(location), str(location))
        cursor.execute(query, value)
    else:
        latitude = None
        longitude = None
    print(f'{web_id} {address}')
    if gmaps:
        try:
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                longitude = geocode_result[0]['geometry']['location']['lng']
                latitude = geocode_result[0]['geometry']['location']['lat']
                location = geocode_result[0]['formatted_address']
                print(location)
                query = ('INSERT OR REPLACE INTO geolocation_google'
                         '(web_id, longitude, latitude, location, complete_response)'
                         'VALUES (?,?,?,?,?)')
                value = (web_id, longitude, latitude, location, str(geocode_result))
                cursor.execute(query, value)
            else:
                print(f"Google geocode returned no results for {web_id}.")
        except googlemaps.exceptions.ApiError as e:
            print(f"Google geocode API error for {web_id}: {e}")
        except Exception as e:
            print(f"Google geocode failed for {web_id}: {e}")
    # If the cleaned street differs from the original, prepend the original as source
    new_beschreibung = beschreibung
    try:
        orig = (original_strasse or '').strip()
    except Exception:
        orig = ''
    if orig and orig != (str(strasse) or '').strip() and orig != clean_strasse:
        prefix = f"(Quelle: {orig}) "
        if not new_beschreibung:
            new_beschreibung = prefix
        elif not new_beschreibung.startswith(prefix):
            new_beschreibung = prefix + new_beschreibung

    # Persist flags and original street into gebaeudebrueter. Columns may be added via migration helper.
    query = ('UPDATE gebaeudebrueter SET new=0, strasse_original=?, has_comma=?, has_slash=?, has_range=?, '
             'multiple_numbers=?, multiple_streets=?, kept_text_after_number=?, beschreibung=? WHERE web_id=?')
    value = (
        original_strasse,
        flags.get('has_comma', 0),
        flags.get('has_slash', 0),
        flags.get('has_range', 0),
        flags.get('multiple_numbers', 0),
        flags.get('multiple_streets', 0),
        flags.get('kept_text_after_number', 0),
        new_beschreibung,
        web_id,
    )
    try:
        cursor.execute(query, value)
    except sqlite3.OperationalError as e:
        # If columns do not exist yet, fall back to updating only new flag.
        print(f"DB update warning (missing columns?): {e}. Updating only new flag.")
        query2 = ('UPDATE gebaeudebrueter set new=0 where web_id=?')
        cursor.execute(query2, (web_id,))
    sqliteConnection.commit()
    print(f'{len(data)}, {index}')
    index += 1
    time.sleep(0.5)

if (sqliteConnection):
    sqliteConnection.close()
