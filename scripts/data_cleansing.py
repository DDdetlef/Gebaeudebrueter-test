import sqlite3
import pandas as pd
import json
import openpyxl

try:
    sqliteConnection = sqlite3.connect('brueter.sqlite')
    cursor = sqliteConnection.cursor()
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)


query = ('SELECT gebaeudebrueter.web_id, plz, geolocation_google.complete_response, '
         'geolocation_osm.complete_response from gebaeudebrueter LEFT JOIN geolocation_osm ON '
         'gebaeudebrueter.web_id = geolocation_osm.web_id LEFT JOIN geolocation_google ON '
         'gebaeudebrueter.web_id = geolocation_google.web_id')


cursor.execute(query)
data = cursor.fetchall()

output = []
for dataset in data:
    (web_id, plz, google_json, osm) = dataset
    # make JSON parsing robust: some rows have None/empty or malformed data
    google_plz = 0
    try:
        google_json_s = str(google_json).replace("'","\"")
        google_json_s = google_json_s.replace('True', '1')
        if google_json_s and google_json_s not in ('None', 'NoneType'):
            google_response = json.loads(google_json_s)
            if (isinstance(google_response, list) and len(google_response) > 0
                    and isinstance(google_response[0], dict)):
                for el in google_response[0].get('address_components', []):
                    types = el.get('types', [])
                    if types and types[0] == 'postal_code':
                        try:
                            google_plz = int(el.get('long_name', 0))
                        except Exception:
                            google_plz = 0
    except Exception:
        # leave google_plz as 0 on any parse error
        google_plz = 0

    osm_response = str(osm).split(',')
    try:
        osm_plz = int(osm_response[-2])
    except:
        osm_plz = 0
    if google_plz == plz and osm_plz == plz:
        equal = 1
    else:
        equal = 0
    output.append((web_id, plz, google_plz, osm_plz, equal))

df = pd.DataFrame(output)
df.to_excel('analyse_plz.xlsx')
# df = pd.read_sql_query("SELECT * from surveys", sqliteConnection)
