import runpy

runpy.run_path('scripts/generateLocationMap.py', run_name='__main__')


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
