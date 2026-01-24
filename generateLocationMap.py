import geopandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
import folium

df = pd.read_file(
    'C:\\Users\\Anita\\Documents\\NABU\\Gebaudebrueter\\Kontrolle_Onlineformular_2020_mit Kontrollnamen.csv')

locator = Nominatim(user_agent="myGeocode")
#geocode = RateLimiter(locator.geocode, min_delay_seconds=1)
longitude = [None] * df.shape[0]
latitude = [None] * df.shape[0]
for index, row in df.iterrows():
    ort = str(row['Straße']) + ', ' + str(row['Bezirk']) + ', Berlin, Deutschland'
    location = locator.geocode(ort)
    if location is not None:
        latitude[index] = location.latitude
        longitude[index] = location.longitude
    else:
        latitude[index] = "52.4739285"
        longitude[index] = "13.4553784"

df['long'] = longitude
df['lat'] = latitude

map1 = folium.Map(
    location=[52.5163,13.3777],
    tiles='cartodbpositron',
    zoom_start=12,
)

df.apply(lambda row:folium.Marker(location=[row["lat"], row["long"]],
                                  popup= folium.Popup('<b>Adresse</b><br/>' + str(row['Straße']) + ', ' + str(row['Bezirk']) +
                                         '<br/><br/><b>Meldung</b><br/>' + row['Meldung'] +
                                         '<br/><br/><b>Datum der Meldung</b><br/>' + row['Datum der Meldung'] +
                                         '<br/><br/><b>Bemerkung</b><br/>' + row['Bemerkung'] +
                                         '<br/><br/><b>Melder</b><br/>' + row['Melder'] +
                                         '<br/><br/><b>Melderangaben</b><br/>' + row['Melderangaben'] +
                                         '<br/><br/><b>Kontrollangaben</b><br/>' + row['Kontrollangaben'] +
                                         '<br/><br/><b>Kontrollperson</b><br/>' + row['Kontrollperson']
                                                     ,max_width=450 ) ,
                                  tooltip='Details').add_to(map1), axis=1)


map1.save('GebaeudebrueterMeldungen.html')


# print("Latitude = {}, Longitude = {}".format(dflatitude, location.longitude))
# print(df['latitude'](0))
# 1 - conveneint function to delay between geocoding calls
# geocode = RateLimiter(locator.geocode, min_delay_seconds=1)
# 2- - create location column
# df['location'] = df['ADDRESS'].apply(geocode)
# 3 - create longitude, laatitude and altitude from location column (returns tuple)
# df['point'] = df['location'].apply(lambda loc: tuple(loc.point) if loc else None)
# 4 - split point column into latitude, longitude and altitude columns
# df[['latitude', 'longitude', 'altitude']] = pd.DataFrame(df['point'].tolist(), index=df.index)
