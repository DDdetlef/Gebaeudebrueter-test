import sqlite3
from pathlib import Path
import re
import csv

DB = Path('brueter.sqlite')
DOCS = Path('docs')
OUT = Path('reports') / 'omitted_from_maps.csv'

def geolocated_web_ids(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute('''
        SELECT DISTINCT g.web_id
        FROM gebaeudebrueter g
        LEFT JOIN geolocation_osm o ON g.web_id=o.web_id
        LEFT JOIN geolocation_google gg ON g.web_id=gg.web_id
        WHERE o.web_id IS NOT NULL OR gg.web_id IS NOT NULL
    ''')
    rows = cur.fetchall()
    con.close()
    return set(r[0] for r in rows)

def ids_in_html(path: Path):
    if not path.exists():
        return set()
    txt = path.read_text(encoding='utf-8', errors='ignore')
    ids = set()
    # pattern matches index.php?ID=1234
    for m in re.findall(r'index\.php\?ID=(\d+)', txt):
        ids.add(int(m))
    # also fallback: anchor text that is just the id (e.g., >1208<)
    for m in re.findall(r'>(\d{3,6})<', txt):
        ids.add(int(m))
    return ids

def main():
    if not DB.exists():
        print(f'ERROR: DB not found at {DB}')
        return
    geo_ids = geolocated_web_ids(DB)
    species_html = DOCS / 'GebaeudebrueterBerlinBySpecies.html'
    meldungen_html = DOCS / 'GebaeudebrueterMeldungen.html'
    ids_species = ids_in_html(species_html)
    ids_meldungen = ids_in_html(meldungen_html)
    html_ids = ids_species.union(ids_meldungen)

    omitted = sorted(geo_ids - html_ids)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['web_id'])
        for wid in omitted:
            writer.writerow([wid])

    print(f'Total geolocated rows: {len(geo_ids)}')
    print(f'Total IDs in HTML: {len(html_ids)}')
    print(f'Omitted count: {len(omitted)}')
    print(f'Report written to {OUT}')

if __name__ == '__main__':
    main()
