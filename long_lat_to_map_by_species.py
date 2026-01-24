import folium
from folium import plugins
import sqlite3
from datetime import datetime
from datetime import date

try:
    sqliteConnection = sqlite3.connect('brueter.sqlite')
    cursor = sqliteConnection.cursor()
except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)

map1 = folium.Map(
    location=[52.5163,13.3777],
    tiles=None,
    zoom_start=12
)
today = date.today().strftime('%d.%m.%Y')
folium.TileLayer('cartodbpositron', control=False, name='erstellt am ' + today + '<br/>Art').add_to(map1)

marker_cluster = plugins.MarkerCluster(control=False)
map1.add_child(marker_cluster)
mauersegler_grp = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Mauersegler')
sperling_grp = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Sperling')
schwalbe_grp = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Schwalbe')
fledermaus_grp = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Fledermaus')
star_grp = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Star')
andere_grp = folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Andere')

map1.add_child(mauersegler_grp)
map1.add_child(sperling_grp)
map1.add_child(schwalbe_grp)
map1.add_child(fledermaus_grp)
map1.add_child(star_grp)
map1.add_child(andere_grp)

positions = []
popups = []
colors = []
url = 'http://www.gebaeudebrueter-in-berlin.de/index.php'

query = ("SELECT gebaeudebrueter.web_id, bezirk, plz, ort, strasse, anhang, erstbeobachtung, beschreibung, besonderes,"
         "mauersegler, kontrolle, sperling, ersatz, schwalbe, wichtig,"
         "star, fledermaus, verloren, andere, "
         "geolocation_osm.longitude AS osm_longitude, geolocation_osm.latitude AS osm_latitude, "
         "geolocation_google.longitude AS google_longitude, geolocation_google.latitude AS google_latitude "
         "FROM gebaeudebrueter "
         "LEFT JOIN geolocation_osm ON gebaeudebrueter.web_id = geolocation_osm.web_id "
         "LEFT JOIN geolocation_google ON gebaeudebrueter.web_id = geolocation_google.web_id")
cursor.execute(query)
data = cursor.fetchall()
for dataset in data:
    (web_id, bezirk, plz, ort, strasse, anhang, erstbeobachtung, beschreibung, besonderes, mauersegler,
     kontrolle, sperling, ersatz, schwalbe, wichtig, star, fledermaus, verloren, andere,
     osm_longitude, osm_latitude, google_longitude, google_latitude) = dataset

    if web_id == 1784:
        continue
    color = 'orange'
    fund = 'andere Art'
    grp = andere_grp
    if mauersegler:
        color='blue'
        fund = 'Mauersegler'
        grp = mauersegler_grp
    if sperling:
        color='green'
        fund = 'Sperling'
        grp = sperling_grp
    if schwalbe:
        color='purple'
        fund = 'Schwalbe'
        grp = schwalbe_grp
    if fledermaus:
        color = 'black'
        fund = 'Fledermaus'
        grp = fledermaus_grp
    if star:
        color = 'darkred'
        fund = 'Star'
        grp = star_grp
    # if row['Andere']:
    #     color = 'orange'
    #     fund = 'andere Art'
    #     grp = andere
    # prefer OSM coords, fallback to Google coords; treat string 'None' as missing
    latitude = None
    longitude = None
    if osm_latitude and str(osm_latitude) != 'None' and osm_longitude and str(osm_longitude) != 'None':
        latitude = osm_latitude
        longitude = osm_longitude
    elif google_latitude and str(google_latitude) != 'None' and google_longitude and str(google_longitude) != 'None':
        latitude = google_latitude
        longitude = google_longitude

    icon = folium.Icon(color=color)
    if latitude is None or longitude is None:
        continue

    if ersatz:
        ersatz_text = '<br/><br/><b>Hier wurden Ersatzmaßnahmen errichtet</b>'
    else:
        ersatz_text = ''

    try:
        erstbeobachtung = datetime.strptime(erstbeobachtung,'%Y-%m-%d %H:%M:%S')
        erstbeobachtung_text = erstbeobachtung.strftime('%d.%m.%Y')
    except:
        erstbeobachtung_text = 'unbekannt'

    besonderes_text  = '<br/><br/><b>Besonderes</b><br/>' + besonderes if besonderes else ''

    popup = folium.Popup('<b>Fund: </b>' + fund + '<br/><br/><b>Adresse</b><br/>' + str(strasse) + ', ' + str(plz) + ' ' + str(ort) +
                         '<br/><br/><b>Erstbeobachtung: </b>' + erstbeobachtung_text +
                         '<br/><br/><b>Beschreibung</b><br/>' + beschreibung +
                         besonderes_text +
                         ersatz_text +
                         '<br/><br/><b>Link zur Datenbank</b><br/><a href=' + url + '?ID=' + str(web_id) + '>' + str(web_id) + '</a>'
                         , max_width=450)
    try:
        folium.Marker(location=[latitude, longitude], popup=popup, tooltip=fund, icon=icon).add_to(grp)
    except:
        print('bla')


folium.LayerControl(collapsed=False, ).add_to(map1)

legend_html = '''
     <div style="position: fixed;
    bottom: 0px; left: 0px; width: 130px; height: 20px;
     border:0px; z-index:9999; font-size:12px; background: white; padding-left: 5px; padding-top: 3px;
     ">erstellt am '''
legend_html = legend_html + today + '</div>'


map1.get_root().html.add_child(folium.Element(legend_html))

map1.save('GebaeudebrueterBerlinBySpecies.html')
if (sqliteConnection):
    sqliteConnection.close()
