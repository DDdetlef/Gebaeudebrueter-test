## Overview

Gebäudebrüter maps for Berlin: data ingestion, geocoding, and interactive maps published via GitHub Pages. This repo now includes a v2 multi‑species marker visualization with filters and clustering.

## Setup

1. Clone the repository
2. Provide API key file `api.key` in the project root (Google Maps for optional geocoding)
3. Ensure Python environment is available (local venv recommended)

## Data Fetch

Run `scripts/nabuPageScraper.py` to fetch entries into `brueter.sqlite`.
- Configure `only_get_new_ids` to fetch either all or only new entries.

## Geocoding

Run `scripts/generateLocationForPageMap.py` to geocode addresses.
- Uses OpenStreetMap (Nominatim) with rate limiting
- Optionally uses Google Maps (requires `api.key`)

## Map Generation

Classic species map:
- Run `scripts/long_lat_to_map_by_species.py` to produce the species‑grouped map.

Multi‑species markers (v2):
- Run:

```bash
scripts/generateMultiSpeciesMap.py
```

Outputs `GebaeudebrueterMultiMarkers.html` (see Publishing below).

## Filters & Logic (v2)

- Species (fill) and Status (rim/badge) filters
- Special rule + AND logic:
  - If no species selected → show nothing
  - If species selected and no status selected → show species matches
  - If species and status selected → location must match both
- Clusters rebuild on filter changes; counts/layout update accordingly

## Publishing (GitHub Pages)

GitHub Pages should point to the branch with `docs/` (e.g. `feature/multi-species-markers-v2` + `docs`).

Publish the generated HTML by copying to `docs/`:

```powershell
Copy-Item -Path "GebaeudebrueterMultiMarkers.html" -Destination "docs/GebaeudebrueterMultiMarkers.html" -Force
```

The root `index.html` links to the current maps; `docs/index.html` provides the Pages landing page.

## Repository Hygiene

- Generated HTML in the repo root is ignored; `docs/` hosts published HTML.
- Local virtual env `.venv/`, caches (`__pycache__/`), and `out/` are ignored.
- Reports/exports and backups are excluded from VCS; see `.gitignore`.

## Notes

- Coordinates prefer OSM; Google is used as fallback when available.
- Marker segments cap at 4 for readability.
- For large updates, run `scripts/ci_publish_maps.py` to regenerate and push docs (if configured).

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
scripts/generateMultiSpeciesMap.py

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
