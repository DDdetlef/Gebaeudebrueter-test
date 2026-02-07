When starting from scratch:
    clone github repository
    copy api key into project folder (file is called api.key)

To generate Berlin map Gebäudebrüter:
    run scripts/nabuPageScraper.py to save all data entries from the Gebäudebrüter database in brueter.sqlite
        option to download all (only_get_new_ids = True) or to only download new entries (only_get_new_ids = False)
    run scripts/generateLocationForPageMap.py to generate gps coordinates using GoogleMaps and OpenStreetMap
    run long_lat_to_map_by_species to generate map with OpenStreetMap coordinates grouped by species
        check if row 50 is still valid as three IDs are removed from the map

## Multi‑Spezies Marker Map (v2)

This version adds segmented, multi‑species markers with status overlays, interactive filters, and cluster‑aware updates.

### Features
- Segmented fill (primary): each marker shows 1–4 segments for present species.
- Status rim + badge (secondary): colored outline and small badge for `Sanierung`, `Ersatzmaßnahme`, `Kontrolle`, `Nicht mehr`.
- Filters with OR logic across groups:
    - A location is visible if species filter OR status filter matches.
    - Within each group, any overlap counts as a match (OR inside group).
    - Empty filter groups are considered “not fulfilled”. If both groups are empty, no markers are shown.
- "Alle" checkboxes: toggle all species or all statuses at once; stays checked only if all individual boxes are checked.
- Cluster‑aware filtering: clusters rebuild when filters change; counts and layout adapt.
- Hover: markers grow slightly with a soft shadow.

### Generate the v2 map

Prerequisites: install Python deps and have `brueter.sqlite` populated.

```bash
# Using the project venv
C:/Users/2andr/Documents/VisualStudioCode_Projekte/Gebaeudebrueter-master/.venv/Scripts/python.exe scripts/generateMultiSpeciesMap.py

# The HTML is written to:
#   GebaeudebrueterMultiMarkers.html
```

Open the generated file in a browser to interact with filters and popups.

### Publishing (GitHub Pages)
- Pages source should point to the branch/folder that contains `docs/` (e.g. `feature/multi-species-markers-v2 / docs`).
- Copy the generated HTML into `docs/` for publishing:

```bash
Copy-Item -Path "GebaeudebrueterMultiMarkers.html" -Destination "docs/GebaeudebrueterMultiMarkers.html" -Force
```

- The docs index links to the new map. You can also set a redirect from the legacy species page to the new view.

### Controls & Behavior
- Filter Arten: select species to render; segments show only selected species present at a location.
- Filter Status: select statuses to render; rim + badge appear only when a selected status is present.
- Visibility rule: visible if (species match) OR (status match). Both groups empty → show nothing.
- Reset: reselects all species + statuses, rebuilds clusters, shows all markers.

### Notes
- Coordinates prefer OSM, then Google if OSM is missing.
- Max 4 species segments are rendered per marker for readability.
- Large filter changes trigger a quick cluster rebuild; counts update after a short delay.
