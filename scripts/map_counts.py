import sqlite3
from pathlib import Path

DB = Path('brueter.sqlite')
DOCS = Path('docs')

def db_counts(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM gebaeudebrueter')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(DISTINCT g.web_id) FROM gebaeudebrueter g JOIN geolocation_osm o ON g.web_id=o.web_id')
    osm = cur.fetchone()[0]
    cur.execute('SELECT COUNT(DISTINCT g.web_id) FROM gebaeudebrueter g JOIN geolocation_google gg ON g.web_id=gg.web_id')
    google = cur.fetchone()[0]
    # rows with any geolocation
    cur.execute('SELECT COUNT(DISTINCT g.web_id) FROM gebaeudebrueter g LEFT JOIN geolocation_osm o ON g.web_id=o.web_id LEFT JOIN geolocation_google gg ON g.web_id=gg.web_id WHERE o.web_id IS NOT NULL OR gg.web_id IS NOT NULL')
    anygeo = cur.fetchone()[0]
    # check if web_id 1784 exists
    cur.execute('SELECT COUNT(*) FROM gebaeudebrueter WHERE web_id=1784')
    has_1784 = cur.fetchone()[0]
    con.close()
    return dict(total=total, osm=osm, google=google, anygeo=anygeo, has_1784=has_1784)

def count_markers_in_file(path: Path):
    if not path.exists():
        return 0
    txt = path.read_text(encoding='utf-8', errors='ignore')
    return txt.count('L.marker(')

def main():
    db = DB
    if not db.exists():
        print(f'ERROR: DB not found at {db}')
        return
    counts = db_counts(db)
    print('DB totals:')
    print(f"- gebaeudebrueter rows: {counts['total']}")
    print(f"- geolocation_osm rows (distinct web_id): {counts['osm']}")
    print(f"- geolocation_google rows (distinct web_id): {counts['google']}")
    print(f"- rows with any geolocation: {counts['anygeo']}")
    print(f"- web_id=1784 present in DB: {counts['has_1784']}")

    # count markers in docs HTML
    species_html = DOCS / 'GebaeudebrueterBerlinBySpecies.html'
    meldungen_html = DOCS / 'GebaeudebrueterMeldungen.html'
    s_markers = count_markers_in_file(species_html)
    m_markers = count_markers_in_file(meldungen_html)
    print('\nMarker counts in docs:')
    print(f"- {species_html}: {s_markers}")
    print(f"- {meldungen_html}: {m_markers}")

    # compare expected vs actual
    expected = counts['anygeo']
    print('\nComparison:')
    print(f"- rows with geolocation (expected markers): {expected}")
    print(f"- markers in species map: {s_markers}")
    print(f"- markers in meldungen map: {m_markers}")
    if s_markers != expected:
        print('\nNOTE: species map marker count differs from DB geolocated rows.')
    else:
        print('\nSpecies map marker count matches DB geolocated rows.')

if __name__ == '__main__':
    main()
