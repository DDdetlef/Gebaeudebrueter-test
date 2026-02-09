import sqlite3
import folium
from folium import plugins

# Zentrale Konfiguration für dieses Skript
CONFIG = {
    'DB_PATH': 'brueter.sqlite',
    'OUTPUT_HTML': 'GebaeudebrueterMeldungen.html',
    'NABU_BASE_URL': 'http://www.gebaeudebrueter-in-berlin.de/index.php',
}

# Generate Meldungen map from database, prefer OSM coords then Google as fallback
try:
    conn = sqlite3.connect(CONFIG['DB_PATH'])
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
except Exception as e:
    raise

map1 = folium.Map(location=[52.5163,13.3777], tiles='cartodbpositron', zoom_start=12)

marker_cluster = plugins.MarkerCluster()
map1.add_child(marker_cluster)

query = ("SELECT b.web_id, b.bezirk, b.plz, b.ort, b.strasse, b.anhang, b.erstbeobachtung, b.beschreibung, b.besonderes, "
         "o.latitude AS osm_latitude, o.longitude AS osm_longitude, gg.latitude AS google_latitude, gg.longitude AS google_longitude "
         "FROM gebaeudebrueter b "
         "LEFT JOIN geolocation_osm o ON b.web_id = o.web_id "
         "LEFT JOIN geolocation_google gg ON b.web_id = gg.web_id "
         "WHERE (b.is_test IS NULL OR b.is_test=0) AND (b.noSpecies IS NULL OR b.noSpecies=0)")

cur.execute(query)
rows = cur.fetchall()
url = CONFIG['NABU_BASE_URL']
count = 0
for r in rows:
    web_id = r['web_id']
    # test rows are excluded via the SQL WHERE clause (is_test)
    # prefer osm, fallback to google
    lat = None
    lon = None
    if r['osm_latitude'] is not None and str(r['osm_latitude']) != 'None':
        lat = r['osm_latitude']
        lon = r['osm_longitude']
    elif r['google_latitude'] is not None and str(r['google_latitude']) != 'None':
        lat = r['google_latitude']
        lon = r['google_longitude']
    if lat is None or lon is None:
        continue
    try:
        latf = float(lat)
        lonf = float(lon)
    except Exception:
        continue

    popup_html = (
        f"<b>Adresse</b><br/>{r['strasse']}, {r['plz']} {r['ort']}"
        f"<br/><br/><b>Erstbeobachtung</b><br/>{(str(r['erstbeobachtung']) if r['erstbeobachtung'] else 'unbekannt')}"
        f"<br/><br/><b>Beschreibung</b><br/>{(r['beschreibung'] or '')}"
        f"<br/><br/><b>Link zur Datenbank</b><br/><a href={url}?ID={web_id}>{web_id}</a>"
    )

    folium.Marker(location=[latf, lonf], popup=folium.Popup(popup_html, max_width=450)).add_to(marker_cluster)
    count += 1

map1.get_root().html.add_child(folium.Element('<div style="position: fixed; bottom: 0; left: 0; background: white; padding: 4px; z-index:9999">Markers: ' + str(count) + '</div>'))
map1.save(CONFIG['OUTPUT_HTML'])
conn.close()
