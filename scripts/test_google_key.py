import requests
import urllib.parse

KEY = 'AIzaSyAFiuxkZPm1LOEjTMS5Y64wU2of6u0QApI'
address = 'Pallasstr. 25, 10781, Berlin'
params = {'address': address, 'key': KEY}
url = 'https://maps.googleapis.com/maps/api/geocode/json?' + urllib.parse.urlencode(params)

print('Request URL:', url)
resp = requests.get(url, timeout=10)
print('HTTP status:', resp.status_code)
try:
    j = resp.json()
    import json
    print('Response JSON:')
    print(json.dumps(j, indent=2, ensure_ascii=False))
except Exception as e:
    print('Failed to parse JSON:', e)
import os
import requests

key_env = os.environ.get('GOOGLE_API_KEY')
key_file = None
if os.path.exists('api.key'):
    with open('api.key') as f:
        key_file = f.read().strip()

print('GOOGLE_API_KEY in env:', 'YES' if key_env else 'NO')
print('api.key file found:', 'YES' if key_file else 'NO')

key_to_use = key_env or key_file
if key_to_use:
    masked = key_to_use
    if len(masked) > 10:
        masked = masked[:4] + '...' + masked[-4:]
    print('Using key (masked):', masked)
    addr = 'Pallasstr. 25, 10781, Berlin, Germany'
    params = {'address': addr, 'key': key_to_use}
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    try:
        r = requests.get(url, params=params, timeout=10)
        j = r.json()
        print('HTTP status:', r.status_code)
        print('Google API status:', j.get('status'))
        if 'error_message' in j:
            print('error_message:', j.get('error_message'))
        if j.get('results'):
            res = j['results'][0]
            loc = res.get('geometry', {}).get('location')
            print('First result location:', loc)
    except Exception as e:
        print('Request failed:', str(e))
else:
    print('No key available to test.')
