import sqlite3
import folium
from folium import plugins
import json

# New multi-species marker map with segmented fill (species) and border/icon (status)
# Output: GebaeudebrueterMultiMarkers.html

DB_PATH = 'brueter.sqlite'
OUTPUT_HTML = 'GebaeudebrueterMultiMarkers.html'

# Species → color palette
SPECIES_COLORS = {
    'Mauersegler': '#1f78b4',  # blue
    'Sperling': '#33a02c',     # green
    'Schwalbe': '#6a3d9a',     # purple
    'Fledermaus': '#000000',   # black
    'Star': '#b15928',         # brown
    'Andere': '#ff7f00'        # orange
}

# Status → color + short label/icon text
STATUS_INFO = {
    'verloren': {'label': 'Nicht mehr', 'color': '#616161', 'short': '×'},
    'sanierung': {'label': 'Sanierung', 'color': '#e31a1c', 'short': 'S'},
    'ersatz': {'label': 'Ersatzmaßn.', 'color': '#00897b', 'short': 'E'},
    'kontrolle': {'label': 'Kontrolle', 'color': '#1976d2', 'short': 'K'},
}

# Priority order for primary status selection (first match wins)
STATUS_PRIORITY = ['verloren', 'sanierung', 'ersatz', 'kontrolle']

# Neutral fill for Status-only mode
NEUTRAL_FILL = '#cccccc'


def pick_primary_status(row):
  statuses = []
  for key in STATUS_PRIORITY:
    try:
      val = row[key]
    except Exception:
      val = None
    if val:
      statuses.append(key)
  primary = statuses[0] if statuses else None
  return primary, statuses


def species_list_from_row(row):
  def safe_bool(col):
    try:
      return bool(row[col])
    except Exception:
      return False
  flags = {
    'Mauersegler': safe_bool('mauersegler'),
    'Sperling': safe_bool('sperling'),
    'Schwalbe': safe_bool('schwalbe'),
    'Fledermaus': safe_bool('fledermaus'),
    'Star': safe_bool('star'),
    'Andere': safe_bool('andere'),
  }
  return [name for name, flag in flags.items() if flag]


def conic_gradient_for_species(species):
  # Up to 4 segments; equal-sized
  if not species:
    return "background: #cccccc;"
  n = min(len(species), 4)
  seg_angle = 360 / n
  stops = []
  for i, sp in enumerate(species[:n]):
      start = round(i * seg_angle, 2)
      end = round((i + 1) * seg_angle, 2)
      color = SPECIES_COLORS.get(sp, '#9e9e9e')
      stops.append(f"{color} {start}deg {end}deg")
  return f"background: conic-gradient({', '.join(stops)});"


def build_divicon_html(species, status_key, all_statuses, address_text):
    # Marker base styles
    gradient_style = conic_gradient_for_species(species)
    status_color = STATUS_INFO[status_key]['color'] if status_key else '#9e9e9e'
    status_short = STATUS_INFO[status_key]['short'] if status_key else ''
    status_label = STATUS_INFO[status_key]['label'] if status_key else ''

    # Data attributes for JS toggling/filtering
    data_species = json.dumps(species, ensure_ascii=False)
    data_statuses = json.dumps(all_statuses, ensure_ascii=False)

    # DivIcon HTML with inline styles + datasets
    html = f'''
    <div class="ms-marker"
         data-species='{data_species}'
         data-statuses='{data_statuses}'
         data-statuscolor="{status_color}"
         data-statuslabel="{status_label}"
         data-address="{address_text}"
         style="{gradient_style} outline: 2px solid {status_color}; outline-offset: 2px; width: 26px; height: 26px; border-radius: 50%; position: relative; box-shadow: 0 0 0 rgba(0,0,0,0); transition: transform 0.12s ease, box-shadow 0.12s ease;">
        <div class="ms-badge" style="position:absolute; right:-4px; bottom:-4px; background:{status_color}; color:#fff; border-radius:8px; font-size:10px; line-height:10px; padding:2px 4px;">{status_short}</div>
    </div>
    '''
    return html


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Base map
    m = folium.Map(location=[52.5163, 13.3777], tiles='cartodbpositron', zoom_start=12)
    marker_cluster = plugins.MarkerCluster()
    m.add_child(marker_cluster)

    # Query includes species + statuses and both OSM + Google coords
    query = (
        "SELECT b.web_id, b.bezirk, b.plz, b.ort, b.strasse, b.anhang, b.erstbeobachtung, b.beschreibung, b.besonderes, "
        "b.mauersegler, b.sperling, b.schwalbe, b.fledermaus, b.star, b.andere, "
        "b.sanierung, b.ersatz, b.kontrolle, b.verloren, "
        "o.latitude AS osm_latitude, o.longitude AS osm_longitude, gg.latitude AS google_latitude, gg.longitude AS google_longitude "
        "FROM gebaeudebrueter b "
        "LEFT JOIN geolocation_osm o ON b.web_id = o.web_id "
        "LEFT JOIN geolocation_google gg ON b.web_id = gg.web_id "
        "WHERE (b.is_test IS NULL OR b.is_test=0) AND (b.noSpecies IS NULL OR b.noSpecies=0)"
    )
    cur.execute(query)

    rows = cur.fetchall()
    url = 'http://www.gebaeudebrueter-in-berlin.de/index.php'

    count = 0
    for r in rows:
        # choose coords preferring OSM
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

        species = species_list_from_row(r)
        primary_status, all_statuses = pick_primary_status(r)

        # Popup content
        fund_text = ', '.join(species) if species else 'andere Art'
        status_names = [STATUS_INFO[k]['label'] for k in all_statuses]
        status_text = ', '.join(status_names) if status_names else '—'
        popup_html = (
            f"<b>Arten</b><br/>{fund_text}"
            f"<br/><br/><b>Status</b><br/>{status_text}"
            f"<br/><br/><b>Adresse</b><br/>{r['strasse']}, {r['plz']} {r['ort']}"
            f"<br/><br/><b>Erstbeobachtung</b><br/>{(str(r['erstbeobachtung']) if r['erstbeobachtung'] else 'unbekannt')}"
            f"<br/><br/><b>Beschreibung</b><br/>{(r['beschreibung'] or '')}"
            f"<br/><br/><b>Link zur Datenbank</b><br/><a href={url}?ID={r['web_id']}>{r['web_id']}</a>"
        )

        address_text = f"{r['strasse']}, {r['plz']} {r['ort']}"
        icon_html = build_divicon_html(species, primary_status, all_statuses, address_text)
        icon = folium.DivIcon(html=icon_html, icon_size=(26, 26), icon_anchor=(13, 13), class_name='ms-div-icon')

        tooltip_text = 'Mehrere Arten' if len(species) > 1 else (species[0] if species else 'Andere')
        folium.Marker(
            location=[latf, lonf],
            popup=folium.Popup(popup_html, max_width=450),
            tooltip=tooltip_text,
            icon=icon
        ).add_to(marker_cluster)
        count += 1

    # Controls and dynamic behavior (toggle modes + filters + hover)
    controls_html = '''
    <style>
    .leaflet-container .ms-marker:hover { transform: scale(1.15); box-shadow: 0 1px 6px rgba(0,0,0,0.35); }
    .ms-control { position: fixed; top: 10px; left: 10px; background: #fff; padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-family: sans-serif; }
    .ms-control h3 { margin: 0 0 6px 0; font-size: 15px; }
    .ms-info { display: none; margin:6px 0 8px 0; font-size:12px; max-width:280px; }
    .ms-info a { color: #0b66c3; text-decoration: underline; }
    .ms-control h4 { margin: 0 0 6px 0; font-size: 13px; }
    .ms-row { display:flex; gap:8px; align-items:center; margin: 6px 0; }
    .ms-row label { font-size: 12px; }
    .ms-badge { display: none; }
    .ms-hidden { display: none !important; }
    .leaflet-marker-icon.ms-div-icon {
      background: transparent !important;
      background-image: none !important;
      border: none !important;
      box-shadow: none !important;
      overflow: visible !important;
    }
    .leaflet-marker-icon.ms-div-icon::before,
    .leaflet-marker-icon.ms-div-icon::after { display: none !important; }
    </style>
    <div class="ms-control">
      <h3>Karte der Gebäudebrüter in Berlin</h3>
      <div><a href="#" id="ms-more-info">Mehr Infos hier</a></div>
      <div class="ms-info" id="ms-more-info-popup">
        <p>Diese Karte zeigt Standorte von Gebäudebrütern in der Stadt, die in der Online-Datenbank des NABU-Landesverbands, AG Gebäudebrüterschutz erfasst wurden (zur Online-Datenbank: <a href="http://www.gebaeudebrueter-in-berlin.de/index.php" target="_blank" rel="noopener">http://www.gebaeudebrueter-in-berlin.de/index.php</a>).</p>
        <p>Nutzen Sie die Filter auf der linken Seite, um die angezeigten Arten und den Status von Nachweisen (z. B. Sanierung, Kontrolle, Ersatzmaßnahmen) gezielt ein- oder auszublenden.</p>
        <p>Klicken Sie auf einen Standort-Marker, um weitere Informationen zu den dort erfassten Arten und Maßnahmen zu erhalten.</p>
      </div>
      <h4>Filter Arten</h4>
      <div class="ms-row" id="ms-species-row"></div>
      <h4>Filter Status</h4>
      <div class="ms-row" id="ms-status-row"></div>
      <div class="ms-row">
        <button id="ms-reset" title="Alle Marker zeigen">Reset</button>
      </div>
    </div>
    <script>
    (function(){
      var SPECIES_COLORS_JS = %SPECIES_COLORS_JSON%;
      var STATUS_INFO_JS = %STATUS_INFO_JSON%;
      // Cluster-aware filtering support
      var MS = { map:null, cluster:null, markers:[], ready:false };
      function resolveMapAndCluster(cb){
        function tryResolve(){
          var mapVarName = Object.keys(window).find(function(k){ return /^map_/.test(k); });
          var map = mapVarName ? window[mapVarName] : null;
          if(!map){ return setTimeout(tryResolve, 150); }
          var cluster = null;
          map.eachLayer(function(l){ if(l instanceof L.MarkerClusterGroup){ cluster = l; } });
          if(!cluster){ return setTimeout(tryResolve, 150); }
          cb(map, cluster);
        }
        tryResolve();
      }
      function parseMetaFromIconHtml(html){
        var temp = document.createElement('div'); temp.innerHTML = (html||'').trim();
        var el = temp.querySelector('.ms-marker');
        var species = []; var statuses = []; var statusColor = '#9e9e9e';
        if(el){
          try{ species = JSON.parse(el.getAttribute('data-species')||'[]'); }catch(e){}
          try{ statuses = JSON.parse(el.getAttribute('data-statuses')||'[]'); }catch(e){}
          statusColor = el.getAttribute('data-statuscolor') || '#9e9e9e';
        }
        return { species: species, statuses: statuses, statusColor: statusColor };
      }
      function initMarkers(){
        MS.markers = MS.cluster.getLayers();
        MS.markers.forEach(function(m){
          var html = (m.options && m.options.icon && m.options.icon.options && m.options.icon.options.html) || '';
          m._ms = parseMetaFromIconHtml(html);
        });
        MS.ready = true;
      }
      // More info popup toggle
      document.addEventListener('click', function(ev){
        var t = ev.target || ev.srcElement;
        if(t && t.id === 'ms-more-info'){
          ev.preventDefault();
          var p = document.getElementById('ms-more-info-popup');
          if(p){ p.style.display = (p.style.display === 'block') ? 'none' : 'block'; }
        }
      });
      function intersection(a, b){ return a.filter(function(x){ return b.indexOf(x) !== -1; }); }
      function computeGradient(species){
        if(!species || !species.length){ return '#cccccc'; }
        var n = Math.min(species.length, 4);
        var seg = 360 / n;
        var stops = [];
        for(var i=0;i<n;i++){
          var sp = species[i];
          var color = SPECIES_COLORS_JS[sp] || '#9e9e9e';
          var start = (i*seg).toFixed(2);
          var end = ((i+1)*seg).toFixed(2);
          stops.push(color + ' ' + start + 'deg ' + end + 'deg');
        }
        return 'conic-gradient(' + stops.join(', ') + ')';
      }
      function applyVisualsToMarker(m, selectedSpecies, selectedStatus){
        var sp = m._ms.species || [];
        var st = m._ms.statuses || [];
        var spSel = selectedSpecies.length ? intersection(sp, selectedSpecies) : [];
        var el = m._icon;
        var inner = el ? el.querySelector('.ms-marker') : null;
        if(inner){
          inner.style.background = computeGradient(spSel);
          var stSel = selectedStatus.length ? intersection(st, selectedStatus) : [];
          var color = 'transparent';
          if(stSel.length){
            var key = stSel[0];
            color = (STATUS_INFO_JS[key] && STATUS_INFO_JS[key].color) || (m._ms.statusColor || '#9e9e9e');
          }
          inner.style.outline = '2px solid ' + color;
          var badge = inner.querySelector('.ms-badge'); if(badge){ badge.style.display = stSel.length ? 'block' : 'none'; badge.style.background = color; }
        }
      }
      function rebuildCluster(selectedSpecies, selectedStatus){
        if(!MS.ready){ return; }
        MS.cluster.clearLayers();
        var toAdd = [];
        for(var i=0;i<MS.markers.length;i++){
          var m = MS.markers[i];
          var sp = m._ms.species || [];
          var st = m._ms.statuses || [];
          var speciesMatch = selectedSpecies.length ? intersection(sp, selectedSpecies).length > 0 : false;
          var statusMatch = selectedStatus.length ? intersection(st, selectedStatus).length > 0 : false;
          // Special rule:
          // - If no species selected → show nothing
          // - If species selected and no status selected → show species-only matches
          // - Else (both selected) → AND across groups
          var speciesSelected = selectedSpecies.length > 0;
          var statusSelected = selectedStatus.length > 0;
          var visible = false;
          if(!speciesSelected){
            visible = false;
          } else if(speciesSelected && !statusSelected){
            visible = speciesMatch;
          } else {
            visible = speciesMatch && statusMatch;
          }
          if(visible){ toAdd.push(m); }
        }
        toAdd.forEach(function(m){ MS.cluster.addLayer(m); });
        setTimeout(function(){ MS.cluster.getLayers().forEach(function(m){ applyVisualsToMarker(m, selectedSpecies, selectedStatus); }); }, 75);
      }
      function applyMode(){
        var els = document.querySelectorAll('.ms-marker');
        els.forEach(function(el){
          var statusColor = el.getAttribute('data-statuscolor') || '#9e9e9e';
          var species = JSON.parse(el.getAttribute('data-species') || '[]');
          // Always show both: species gradient + status border/badge
          el.style.background = getGradient(species);
          el.style.outline = '2px solid ' + statusColor;
          var badge = el.querySelector('.ms-badge');
          if(badge) badge.style.display = 'block';
        });
      }
      function getGradient(species){
        if(!species || !species.length){ return '#cccccc'; }
        var n = Math.min(species.length, 4);
        var seg = 360 / n;
        var stops = [];
        for(var i=0;i<n;i++){
          var sp = species[i];
          var color = SPECIES_COLORS_JS[sp] || '#9e9e9e';
          var start = (i*seg).toFixed(2);
          var end = ((i+1)*seg).toFixed(2);
          stops.push(color + ' ' + start + 'deg ' + end + 'deg');
        }
        return 'conic-gradient(' + stops.join(', ') + ')';
      }
      // build filter checkboxes
      function buildFilters(){
        var sRow = document.getElementById('ms-species-row');
        // 'Alle' for species
        var sAllWrap = document.createElement('label'); sAllWrap.style.display='flex'; sAllWrap.style.alignItems='center';
        var sAll = document.createElement('input'); sAll.type='checkbox'; sAll.id='ms-species-all'; sAll.checked=true;
        sAllWrap.appendChild(sAll); sAllWrap.appendChild(document.createTextNode(' Alle'));
        sRow.appendChild(sAllWrap);
        Object.keys(SPECIES_COLORS_JS).forEach(function(name){
          var id = 'ms-sp-' + name;
          var wrap = document.createElement('label');
          wrap.style.display = 'flex';
          wrap.style.alignItems = 'center';
          var cb = document.createElement('input');
          cb.type = 'checkbox'; cb.value = name; cb.id = id; cb.className = 'ms-filter-species'; cb.checked = true;
          var swatch = document.createElement('span');
          swatch.style.display = 'inline-block'; swatch.style.width = '12px'; swatch.style.height = '12px'; swatch.style.borderRadius = '50%'; swatch.style.margin = '0 6px'; swatch.style.background = SPECIES_COLORS_JS[name];
          wrap.appendChild(cb); wrap.appendChild(swatch); wrap.appendChild(document.createTextNode(name));
          sRow.appendChild(wrap);
        });
        var stRow = document.getElementById('ms-status-row');
        // 'Alle' for status
        var stAllWrap = document.createElement('label'); stAllWrap.style.display='flex'; stAllWrap.style.alignItems='center';
        var stAll = document.createElement('input'); stAll.type='checkbox'; stAll.id='ms-status-all'; stAll.checked=true;
        stAllWrap.appendChild(stAll); stAllWrap.appendChild(document.createTextNode(' Alle'));
        stRow.appendChild(stAllWrap);
        Object.keys(STATUS_INFO_JS).forEach(function(key){
          var info = STATUS_INFO_JS[key];
          var id = 'ms-st-' + key;
          var wrap = document.createElement('label');
          wrap.style.display = 'flex'; wrap.style.alignItems = 'center';
          var cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = key; cb.id = id; cb.className = 'ms-filter-status'; cb.checked = true;
          var swatch = document.createElement('span');
          swatch.style.display = 'inline-block'; swatch.style.width = '12px'; swatch.style.height = '12px'; swatch.style.borderRadius = '4px'; swatch.style.margin = '0 6px'; swatch.style.background = info.color;
          wrap.appendChild(cb); wrap.appendChild(swatch); wrap.appendChild(document.createTextNode(info.label));
          stRow.appendChild(wrap);
        });
      }
      function applyFilters(){
        var selectedSpecies = Array.from(document.querySelectorAll('.ms-filter-species:checked')).map(function(el){ return el.value; });
        var selectedStatus = Array.from(document.querySelectorAll('.ms-filter-status:checked')).map(function(el){ return el.value; });
        // Ensure cluster is ready; if not, retry shortly
        if(!MS.ready){
          setTimeout(function(){ rebuildCluster(selectedSpecies, selectedStatus); }, 150);
        } else {
          rebuildCluster(selectedSpecies, selectedStatus);
        }
      }
      function wireFilters(){
        var speciesAll = document.getElementById('ms-species-all');
        var statusAll = document.getElementById('ms-status-all');
        if(speciesAll){
          speciesAll.addEventListener('change', function(){
            var check = this.checked;
            document.querySelectorAll('.ms-filter-species').forEach(function(el){ el.checked = check; });
            applyFilters();
          });
        }
        if(statusAll){
          statusAll.addEventListener('change', function(){
            var check = this.checked;
            document.querySelectorAll('.ms-filter-status').forEach(function(el){ el.checked = check; });
            applyFilters();
          });
        }
        document.querySelectorAll('.ms-filter-species').forEach(function(el){
          el.addEventListener('change', applyFilters);
          el.addEventListener('change', function(){
            var boxes = Array.from(document.querySelectorAll('.ms-filter-species'));
            var allChecked = boxes.every(function(b){ return b.checked; });
            var sAll = document.getElementById('ms-species-all'); if(sAll) sAll.checked = allChecked;
          });
        });
        document.querySelectorAll('.ms-filter-status').forEach(function(el){
          el.addEventListener('change', applyFilters);
          el.addEventListener('change', function(){
            var boxes = Array.from(document.querySelectorAll('.ms-filter-status'));
            var allChecked = boxes.every(function(b){ return b.checked; });
            var stAll = document.getElementById('ms-status-all'); if(stAll) stAll.checked = allChecked;
          });
        });
      }
      // wire controls
      document.getElementById('ms-reset').addEventListener('click', function(){
        document.querySelectorAll('.ms-filter-species, .ms-filter-status').forEach(function(el){ el.checked = true; });
        var speciesAll = document.getElementById('ms-species-all'); if(speciesAll) speciesAll.checked = true;
        var statusAll = document.getElementById('ms-status-all'); if(statusAll) statusAll.checked = true;
        var selectedSpecies = Object.keys(SPECIES_COLORS_JS);
        var selectedStatus = Object.keys(STATUS_INFO_JS);
        rebuildCluster(selectedSpecies, selectedStatus);
      });
      // initial pass
      resolveMapAndCluster(function(map, cluster){ MS.map = map; MS.cluster = cluster; initMarkers(); });
      buildFilters();
      wireFilters();
      setTimeout(function(){
        var selectedSpecies = Object.keys(SPECIES_COLORS_JS);
        var selectedStatus = Object.keys(STATUS_INFO_JS);
        rebuildCluster(selectedSpecies, selectedStatus);
      }, 250);
    })();
    </script>
    '''.replace('%SPECIES_COLORS_JSON%', json.dumps(SPECIES_COLORS, ensure_ascii=False))\
       .replace('%STATUS_INFO_JSON%', json.dumps(STATUS_INFO, ensure_ascii=False))

    m.get_root().html.add_child(folium.Element(controls_html))
    m.get_root().html.add_child(folium.Element('<div style="position: fixed; bottom: 0; left: 0; background: white; padding: 4px; z-index:9999">Markers: ' + str(count) + '</div>'))

    m.save(OUTPUT_HTML)
    conn.close()

if __name__ == '__main__':
    main()
