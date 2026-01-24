from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
import sqlite3
import googlemaps
import time
import os

def list_has_digit(addresses):
    if not isinstance(addresses, list):
        return ''
    for element in addresses:
        if any(map(str.isdigit, element)):
            return str(element)

try:
    sqliteConnection = sqlite3.connect('brueter.sqlite')
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

if not key:
    print('ERROR: No Google API key found. Set environment variable GOOGLE_API_KEY or provide api.key file.')
    raise SystemExit(1)

gmaps = googlemaps.Client(key=key)

cursor.execute('SELECT web_id, strasse, ort, plz from gebaeudebrueter where new=1')
data = cursor.fetchall()
# only updates new entries which are set to new=1

locator = Nominatim(scheme='http', user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36")
geocode = RateLimiter(locator.geocode, min_delay_seconds=1)

index = 0
for (web_id, strasse, ort, plz) in data:
    splitstrasse = strasse.split('/')
    splitstrasse = list_has_digit(splitstrasse)
    splitstrasse = str(splitstrasse).split(',')
    splitstrasse = list_has_digit(splitstrasse)
    splitstrasse = str(splitstrasse).split(',')
    splitstrasse = list_has_digit(splitstrasse)
    address = f'{splitstrasse},{plz},{ort},Deutschland'
    location = geocode(address,timeout=10)
    point = tuple(location.point) if location else (None, None, None)
    latitude = str(point[0])
    longitude = str(point[1])
    query = ('INSERT OR REPLACE INTO geolocation_osm'
             '(web_id, longitude, latitude, location, complete_response)'
             'VALUES (?,?,?,?,?)')
    value = (web_id, longitude, latitude, str(location), str(location))
    cursor.execute(query, value)
    print(f'{web_id} {address}')
    geocode_result = gmaps.geocode(address)
    longitude = geocode_result[0]['geometry']['location']['lng']
    latitude = geocode_result[0]['geometry']['location']['lat']
    location = geocode_result[0]['formatted_address']
    print(location)
    query = ('INSERT OR REPLACE INTO geolocation_google'
             '(web_id, longitude, latitude, location, complete_response)'
             'VALUES (?,?,?,?,?)')
    value = (web_id, longitude, latitude, location, str(geocode_result))
    cursor.execute(query, value)
    query = ('UPDATE gebaeudebrueter set new=0 where web_id=?')
    value = (web_id,)
    cursor.execute(query, value)
    sqliteConnection.commit()
    print(f'{len(data)}, {index}')
    index += 1
    time.sleep(0.5)

if (sqliteConnection):
    sqliteConnection.close()

