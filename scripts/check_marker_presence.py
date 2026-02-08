import sqlite3
import sys
from pathlib import Path

DB='brueter.sqlite'
WEB_ID=2267

def main():
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute('SELECT longitude,latitude,location,complete_response FROM geolocation_osm WHERE web_id=?',(WEB_ID,))
    row=cur.fetchone()
    if not row:
        print(f'No geolocation_osm row for web_id={WEB_ID}')
        return 1
    lon,lat,location,resp = row
    print('geolocation_osm:', 'lon=', lon, 'lat=', lat)
    html_path=Path('GebaeudebrueterMultiMarkers.html')
    if not html_path.exists():
        print('HTML file not found:', html_path)
        return 2
    html=html_path.read_text(encoding='utf-8')
    found=False
    if lon and lat:
        # Search for the float values in either order, with reasonable formatting
        if str(lat) in html and str(lon) in html:
            found=True
    print('marker_in_html:', found)
    # Also try to search for web_id or the location string
    found_by_webid = str(WEB_ID) in html
    print('web_id_in_html:', found_by_webid)
    if location:
        print('location snippet in html:', ('...' + location[:80] + '...') if location in html else 'not present')
    return 0

if __name__ == '__main__':
    sys.exit(main())
