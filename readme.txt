Project: Gebäudebrueter — Daten sammeln, geokodieren und Karten erstellen

Kurzbeschreibung
Dieses Repository zieht Meldungen von der Website www.gebaeudebrueter-in-berlin.de, speichert die Einträge in
einer lokalen SQLite‑Datenbank (`brueter.sqlite`), ermittelt GPS‑Koordinaten (OpenStreetMap & Google Maps)
und erzeugt interaktive Karten (HTML) sowie einfache Statistiken/Analysen.

Kartendarstellung: https://dddetlef.github.io/Gebaeudebrueter-test/

Wichtige Dateien
- `nabuPageScraper.py` : Scraper, der Einträge parst und in `gebaeudebrueter` speichert.
- `initializeDB.sql`  : Schema für `gebaeudebrueter`, `geolocation_google`, `geolocation_osm`.
- `generateLocationForPageMap.py` : Geokodierung (Nominatim + Google Maps) für neue Einträge (`new=1`).
- `long_lat_to_map_by_species.py`  : Erstellt `GebaeudebrueterBerlinBySpecies.html` (Folium, nach Art gruppiert).
- `generateLocationMap.py`        : Alternative Map‑Erzeugung (GeoPandas/Folium) → `GebaeudebrueterMeldungen.html`.
- `data_cleansing.py`            : Vergleich/Analyse der PLZ zwischen Google/OSM und gespeicherter PLZ.
- `anualStats.py`                : Einfache Jahres‑Statistiken und Grafiken (PNG).
- `useful_sql_commands.txt`      : Hilfs‑SQL‑Queries.

Voraussetzungen
- Python 3.8+ (auf Windows getestet)
- Benötigte Python‑Pakete (Beispielinstallation):

```powershell
python -m pip install beautifulsoup4 python-dateutil folium geopy pandas openpyxl googlemaps matplotlib geopandas
```

Hinweis: `sqlite3` ist in der Standardbibliothek. `geopandas` kann zusätzliche Systemabhängigkeiten benötigen.

API‑Key
- Lege einen Google Maps API Key in einer Datei `api.key` (nur der Key als Text, keine Zeilenumbrüche) im Projektordner ab.
  `generateLocationForPageMap.py` liest diese Datei.

Empfohlene Ausführungsreihenfolge
1) `nabuPageScraper.py` – füllt/aktualisiert `gebaeudebrueter` in `brueter.sqlite`.
   - Option: in `nabuPageScraper.py` die Variable `only_get_new_ids` setzen (True = nur neue IDs seit letzter max(web_id)).

```powershell
python scripts/nabuPageScraper.py
```

2) `generateLocationForPageMap.py` – geokodiert Einträge mit `new=1` (benötigt `api.key`) und schreibt in
   `geolocation_osm` und `geolocation_google`.

```powershell
python scripts/generateLocationForPageMap.py
```

3) `long_lat_to_map_by_species.py` oder `generateLocationMap.py` – erzeugt die HTML‑Karten.

```powershell
python scripts/long_lat_to_map_by_species.py
# oder
python scripts/generateLocationMap.py
```

Hilfs‑Skripte
- `data_cleansing.py` : Erzeugt `analyse_plz.xlsx` zum Abgleich der PLZ zwischen Quellen.
- `anualStats.py`     : Erzeugt PNGs mit Jahres‑Statistiken und gestapelter Balkendiagramm‑Ansicht nach Arten.

Betrieb & Pflegehinweise
- Bewahre `api.key` außerhalb des Repos (nicht committen).
- Bei Geokodierungsfehlern: Logs prüfen, ggf. Adressaufbereitung anpassen (Sonderfälle in `generateLocationForPageMap.py`).
- `sanitize_date` in `nabuPageScraper.py` enthält viele manuelle Regeln — bei neuen Formaten erweitern.
- Backup der SQLite‑DB vor Batch‑Läufen empfohlen.

Verbesserungsvorschläge (kurz)
- Retry/Backoff und besseres Logging für Geokodierung.
- Small CLI‑Wrapper (z. B. `run_all.py`) für die Ausführungsreihenfolge und Prüfungen (`api.key` vorhanden?).
- `requirements.txt` oder `pyproject.toml` zur reproduzierbaren Installation.

Kontakt
Bei Fragen oder wenn du möchtest, dass ich das README weiter ausbaue (z. B. `requirements.txt` oder ein
`run_all.py`-Script), sage Bescheid.

GitHub Actions / Automatisches Geocoding
- Wenn du Geocoding in GitHub Actions laufen lassen willst, lege den API‑Key als Repository Secret an:
   - Repo → Settings → Secrets and variables → Actions → New repository secret
   - Name: `GOOGLE_API_KEY`  Value: dein API‑Key
- Es gibt ein Beispiel‑Workflow unter `.github/workflows/geocode.yml`. Er liest `GOOGLE_API_KEY` aus den
   Secrets und führt `python generateLocationForPageMap.py` aus. Da GitHub Actions Runner keine feste Egress‑IP
   haben, ist IP‑Restriktion des Keys hier nicht möglich; beschränke den Key zumindest auf die `Geocoding API`.

Kurze Anleitung zum Testlauf in Actions
1) Push das Repo (ohne `api.key` in commits).
2) In GitHub: Settings → Secrets → Actions → New repository secret → `GOOGLE_API_KEY` setzen.
3) In GitHub → Actions → Geocode → Run workflow (workflow_dispatch) auswählen.

Flags in der Datenbank
- `is_test` (INTEGER, default 0): Kennzeichnet Test‑/Beispieldatensätze; diese werden von den Map‑Generatoren ausgeschlossen.
- `noSpecies` (INTEGER, default 0): Wenn gesetzt, bedeutet das, dass kein konkretes Ziel‑`species` zugeordnet ist — solche Einträge werden bewusst nicht auf den öffentlichen Karten dargestellt.

Einrichtung
- Ein Migrationsskript `scripts/add_db_flags.py` legt die beiden Spalten an (falls noch nicht vorhanden) und markiert `web_id=1784` als `is_test=1`.
