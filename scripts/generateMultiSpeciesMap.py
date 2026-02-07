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
# Controls and dynamic behavior (toggle modes + filters + hover)
controls_html = '''
    <style>
    .leaflet-container .ms-marker:hover { transform: scale(1.15); box-shadow: 0 1px 6px rgba(0,0,0,0.35); }
    /* Control box (desktop + mobile pinned top-right) */
    .ms-control { position: fixed; top: 10px; right: 10px; left: auto; background: #fff; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; z-index: 10002; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-family: sans-serif; max-width:380px; max-height:80vh; overflow:auto; box-sizing:border-box; }
    .ms-control.collapsed { height: 44px; overflow: hidden; }
    .ms-control-header { display:flex; align-items:center; justify-content:space-between; gap:8px; position:relative; padding-right:48px; }
    .ms-control h3 { margin: 0 0 6px 0; font-size: 15px; font-weight: 700; display:inline-block; }
    .ms-link-mode { font-size:12px; color:#0b66c3; padding:4px 6px; border-radius:4px; border:1px solid #e0e0e0; background:#f9f9ff; cursor:pointer; }
    .ms-collapse-btn { background: rgba(255,255,255,0.95); border: 1px solid rgba(0,0,0,0.06); font-size: 18px; padding: 8px; cursor: pointer; line-height: 1; position: absolute; top: 6px; right: 6px; z-index: 10010; touch-action: manipulation; -webkit-tap-highlight-color: transparent; pointer-events: auto; border-radius:6px; }
    .ms-open-sheet-btn { display:none; font-size:13px; padding:6px 8px; border-radius:6px; border:1px solid #ddd; background:#fff; cursor:pointer; }
    .ms-toggle { cursor: pointer; display: inline-flex; align-items: center; gap:6px; font-size:13px; color:#0b66c3; user-select: none; }
    .ms-toggle .arrow { display:inline-block; transition: transform .15s ease; }
    .ms-toggle.open .arrow { transform: rotate(90deg); }
    .ms-modal { position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.45); z-index:10000; display:flex; align-items:center; justify-content:center; }
    .ms-modal-content { background: #fff; padding: 18px 22px; border-radius:10px; max-width:700px; width:calc(100% - 40px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); position:relative; }
    .ms-modal-close { position:absolute; top:8px; right:8px; border:none; background:transparent; font-size:18px; cursor:pointer; }
    /* Bottom-sheet for mobile filters */
    .ms-bottom-sheet { position: fixed; left: 0; right: 0; bottom: 0; max-height: 80vh; background: #fff; box-shadow: 0 -8px 24px rgba(0,0,0,0.18); border-top-left-radius: 12px; border-top-right-radius: 12px; transform: translateY(100%); transition: transform .28s ease; z-index: 10004; overflow: auto; }
    .ms-bottom-sheet.open { transform: translateY(0%); }
    .ms-sheet-header { display:flex; align-items:center; justify-content:space-between; padding: 12px 16px; border-bottom:1px solid #eee; }
    .ms-sheet-handle { width:36px; height:4px; background:#ddd; border-radius:4px; margin:8px auto; }
    .ms-accordion-toggle { width:100%; text-align:left; padding:10px 14px; border:none; background:transparent; font-size:15px; display:flex; align-items:center; justify-content:space-between; cursor:pointer; }
    .ms-accordion-content { padding: 6px 14px 12px 14px; display:none; }
    .ms-accordion-content.open { display:block; }
    .ms-sheet-actions { padding:12px 16px; border-top:1px solid #eee; display:flex; justify-content:flex-end; }
    .ms-sheet-actions button { padding:8px 12px; border-radius:6px; border:1px solid #1976d2; background:#1976d2; color:white; cursor:pointer; }
    .ms-control h4 { margin: 0 0 6px 0; font-size: 13px; }
    .ms-row { display:flex; gap:8px; align-items:center; margin: 6px 0; flex-wrap:wrap; }
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
    @media (max-width: 600px) {
      /* Pin control to top-right on mobile but show compact header and filter button */
      .ms-control { top: 10px; right: 10px; left: auto; bottom: auto; max-width: 92vw; border-radius: 10px; padding: 8px 10px; padding-right: 56px; }
      .ms-control.collapsed { height: 44px; overflow: hidden; }
      .ms-control .ms-row, .ms-control h4 { display: none; }
      .ms-control .ms-toggle { display: none; }
      .ms-control .ms-reset-wrap { display: none; }
      .ms-open-sheet-btn { display:inline-block; }
      .ms-collapse-btn { display:inline-block; }
      /* ensure bottom-sheet is above most elements */
      .ms-bottom-sheet { z-index: 10005; }
    }
    </style>
    <div class="ms-control" id="ms-control">
      <div class="ms-control-header"><h3>Karte der Gebäudebrüter in Berlin</h3>
        <div style="display:flex;align-items:center;gap:8px">
          <div id="ms-link-mode" class="ms-link-mode" title="Wechseln ODER/UND">UND</div>
          <button id="ms-open-sheet" class="ms-open-sheet-btn" title="Filter öffnen">Filter</button>
          <button id="ms-control-toggle" class="ms-collapse-btn" aria-expanded="true" title="Ein-/Ausklappen">☰</button>
        </div>
      </div>
      <div class="ms-row"><div id="ms-more-info-toggle" class="ms-toggle" title="Mehr Informationen anzeigen"><span class="arrow">►</span><span>Mehr Infos / Hilfe</span></div></div>
      <div class="desktop-only">
        <h4>Filter Arten</h4>
        <div class="ms-row" id="ms-species-row"></div>
        <h4>Filter Status</h4>
        <div class="ms-row" id="ms-status-row"></div>
        <div class="ms-row ms-reset-wrap">
          <button id="ms-reset" title="Alle Marker zeigen">Reset</button>
        </div>
      </div>
    </div>
    
    <!-- Bottom-sheet for mobile filters -->
    <div id="ms-bottom-sheet" class="ms-bottom-sheet" aria-hidden="true">
      <div class="ms-sheet-handle"></div>
      <div class="ms-sheet-header">
        <strong>Filter</strong>
        <div id="ms-link-mode-sheet" class="ms-link-mode">UND-Verknüpfung aktiv</div>
      </div>
      <div>
        <button class="ms-accordion-toggle" data-target="ms-species-accordion-content">▸ Arten</button>
        <div id="ms-species-accordion-content" class="ms-accordion-content"></div>
        <button class="ms-accordion-toggle" data-target="ms-status-accordion-content">▸ Status</button>
        <div id="ms-status-accordion-content" class="ms-accordion-content"></div>
      </div>
      <div class="ms-sheet-actions"><button id="ms-apply-filters">Filter anwenden</button></div>
    </div>
    
    <!-- Info modal (separate from legend) -->
    <div id="ms-info-modal" class="ms-modal" style="display:none;">
      <div class="ms-modal-content">
        <button id="ms-info-close" class="ms-modal-close" aria-label="Schließen">✕</button>
        <div class="ms-modal-body">
          <div class="ms-modal-header">
            <h2 class="ms-modal-title">Karte der Gebäudebrüter in Berlin</h2>
          </div>
          <div class="ms-modal-row">
            <div class="ms-modal-text">
              <p>Diese Karte zeigt Standorte von Gebäudebrütern in Berlin an. Gebäudebrüter sind Tiere wie Mauersegler, Schwalben, Sperlinge oder Fledermäuse, die an oder in Gebäuden leben. Die Markierungen stehen für Häuser, an denen Gebäudebrüter gefunden und gemeldet wurden. Die Informationen stammen aus der Online-Datenbank des Projekts Gebäudebrüterschutz der NABU Bezirksgruppe Steglitz-Zehlendorf (<a href="http://www.gebaeudebrueter-in-berlin.de/index.php" target="_blank" rel="noopener">www.gebaeudebrueter-in-berlin.de</a>).</p>
              <p><strong>NABU Bezirksgruppe Steglitz-Zehlendorf</strong></p>
            </div>
            <div class="ms-modal-image">
              <img src="images/Logo%20BezGr%20SteglitzTempelhof%20farb%20(1).jpg" alt="Logo" class="ms-modal-logo-lg" />
            </div>
          </div>
          <h3 class="ms-modal-section-title">Wie funktioniert&#39;s?</h3>
          <div class="ms-modal-text">
            <ol>
              <li>Nutzen Sie die Filter auf der linken Seite, um die angezeigten Arten und den Status von Nachweisen (z. B. Sanierung, Kontrolle, Ersatzmaßnahmen) gezielt ein- oder auszublenden.</li>
              <li>Klicken Sie auf einen Standort-Marker, um weitere Informationen zu den dort erfassten Arten und Maßnahmen zu erhalten.</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
    </div>
    <script>
    (function(){
      var SPECIES_COLORS_JS = %SPECIES_COLORS_JSON%;
      var STATUS_INFO_JS = %STATUS_INFO_JSON%;
      // Cluster-aware filtering support
      var MS = { map:null, cluster:null, markers:[], ready:false };
      var LINK_MODE_JS = 'and'; // 'and' or 'or'
      function resolveMapAndCluster(cb){
        function tryResolve(){
          var mapVarName = Object.keys(window).find(function(k){ return /^map_/.test(k); });
          var map = mapVarName ? window[mapVarName] : null;
          if(!map){ return setTimeout(tryResolve, 150); }
          // ensure zoom control is visible at the map edge
          if(map.zoomControl && typeof map.zoomControl.setPosition === 'function'){
            map.zoomControl.setPosition('bottomright');
          }
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
      // More info modal toggle
      (function(){
        var tog = document.getElementById('ms-more-info-toggle');
        var modal = document.getElementById('ms-info-modal');
        var closeBtn = document.getElementById('ms-info-close');
        if(tog && modal){
          tog.addEventListener('click', function(ev){ ev.preventDefault(); modal.style.display = 'flex'; tog.classList.add('open'); });
          if(closeBtn){ closeBtn.addEventListener('click', function(){ modal.style.display = 'none'; tog.classList.remove('open'); }); }
          modal.addEventListener('click', function(ev){ if(ev.target === modal){ modal.style.display = 'none'; tog.classList.remove('open'); } });
        }
      })();
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
          var speciesSelected = selectedSpecies.length > 0;
          var statusSelected = selectedStatus.length > 0;
          var visible = false;
          // If no filters selected -> show all
          if(!speciesSelected && !statusSelected){ visible = true; }
          else if(LINK_MODE_JS === 'or'){
            // OR across groups
            visible = (speciesSelected && speciesMatch) || (statusSelected && statusMatch);
          } else {
            // AND across groups (when both selected), otherwise single-group matching
            if(speciesSelected && statusSelected){ visible = speciesMatch && statusMatch; }
            else if(speciesSelected){ visible = speciesMatch; }
            else { visible = statusMatch; }
          }
          if(visible){ toAdd.push(m); }
        }
        toAdd.forEach(function(m){ MS.cluster.addLayer(m); });
        setTimeout(function(){ MS.cluster.getLayers().forEach(function(m){ applyVisualsToMarker(m, selectedSpecies, selectedStatus); }); }, 75);
      }
      // build filter checkboxes into desktop and bottom-sheet accordions
      function buildFilters(){
        var sRow = document.getElementById('ms-species-row');
        var sAccordion = document.getElementById('ms-species-accordion-content');
        var stRow = document.getElementById('ms-status-row');
        var stAccordion = document.getElementById('ms-status-accordion-content');
        if(!sRow || !sAccordion || !stRow || !stAccordion) return;
        sRow.innerHTML = ''; sAccordion.innerHTML = '';
        stRow.innerHTML = ''; stAccordion.innerHTML = '';
        // 'Alle' for species
        function makeAllCheckbox(id){ var wrap = document.createElement('label'); wrap.style.display='flex'; wrap.style.alignItems='center'; var cb = document.createElement('input'); cb.type='checkbox'; cb.id = id; cb.checked=true; wrap.appendChild(cb); wrap.appendChild(document.createTextNode(' Alle')); return {wrap:wrap, input:cb}; }
        var sAllDesktop = makeAllCheckbox('ms-species-all'); sRow.appendChild(sAllDesktop.wrap);
        var sAllSheet = makeAllCheckbox('ms-species-all-sheet'); sAccordion.appendChild(sAllSheet.wrap);
        Object.keys(SPECIES_COLORS_JS).forEach(function(name){
          function makeEntry(prefix){
            var id = prefix + '-' + name;
            var wrap = document.createElement('label'); wrap.style.display = 'flex'; wrap.style.alignItems = 'center';
            var cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = name; cb.id = id; cb.className = 'ms-filter-species'; cb.checked = true;
            var swatch = document.createElement('span'); swatch.style.display = 'inline-block'; swatch.style.width = '12px'; swatch.style.height = '12px'; swatch.style.borderRadius = '50%'; swatch.style.margin = '0 6px'; swatch.style.background = SPECIES_COLORS_JS[name];
            wrap.appendChild(cb); wrap.appendChild(swatch); wrap.appendChild(document.createTextNode(name));
            return wrap;
          }
          sRow.appendChild(makeEntry('ms-sp'));
          sAccordion.appendChild(makeEntry('ms-sp-sheet'));
        });
        // 'Alle' for status
        var stAllDesktop = makeAllCheckbox('ms-status-all'); stRow.appendChild(stAllDesktop.wrap);
        var stAllSheet = makeAllCheckbox('ms-status-all-sheet'); stAccordion.appendChild(stAllSheet.wrap);
        Object.keys(STATUS_INFO_JS).forEach(function(key){
          var info = STATUS_INFO_JS[key];
          function makeEntry(prefix){
            var id = prefix + '-' + key;
            var wrap = document.createElement('label'); wrap.style.display = 'flex'; wrap.style.alignItems = 'center';
            var cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = key; cb.id = id; cb.className = 'ms-filter-status'; cb.checked = true;
            var swatch = document.createElement('span'); swatch.style.display = 'inline-block'; swatch.style.width = '12px'; swatch.style.height = '12px'; swatch.style.borderRadius = '4px'; swatch.style.margin = '0 6px'; swatch.style.background = info.color;
            wrap.appendChild(cb); wrap.appendChild(swatch); wrap.appendChild(document.createTextNode(info.label));
            return wrap;
          }
          stRow.appendChild(makeEntry('ms-st'));
          stAccordion.appendChild(makeEntry('ms-st-sheet'));
        });
      }
      function applyFilters(){
        var selectedSpecies = Array.from(document.querySelectorAll('.ms-filter-species:checked')).map(function(el){ return el.value; });
        var selectedStatus = Array.from(document.querySelectorAll('.ms-filter-status:checked')).map(function(el){ return el.value; });
        if(!MS.ready){ setTimeout(function(){ rebuildCluster(selectedSpecies, selectedStatus); }, 150); }
        else { rebuildCluster(selectedSpecies, selectedStatus); }
      }
      function wireFilters(){
        // sync desktop and sheet 'Alle' boxes and checkboxes by class
        document.addEventListener('change', function(ev){ if(ev.target && ev.target.classList){ if(ev.target.classList.contains('ms-filter-species') || ev.target.classList.contains('ms-filter-status')){ var boxes = Array.from(document.querySelectorAll(ev.target.tagName+'[value]')).filter(function(x){ return x.value === ev.target.value && x !== ev.target; }); boxes.forEach(function(b){ b.checked = ev.target.checked; }); }
          // sync 'Alle' behavior
          if(ev.target.id === 'ms-species-all' || ev.target.id === 'ms-species-all-sheet'){ var check = ev.target.checked; document.querySelectorAll('#ms-species-row input[type=checkbox], #ms-species-accordion-content input[type=checkbox]').forEach(function(cb){ if(cb !== ev.target) cb.checked = check; }); }
          if(ev.target.id === 'ms-status-all' || ev.target.id === 'ms-status-all-sheet'){ var check = ev.target.checked; document.querySelectorAll('#ms-status-row input[type=checkbox], #ms-status-accordion-content input[type=checkbox]').forEach(function(cb){ if(cb !== ev.target) cb.checked = check; }); }
        }});
      }
      // wire controls
      document.addEventListener('click', function(ev){
        // open bottom-sheet
        var openBtn = document.getElementById('ms-open-sheet');
        if(ev.target === openBtn){ document.getElementById('ms-bottom-sheet').classList.add('open'); }
        // apply button
        if(ev.target.id === 'ms-apply-filters'){ applyFilters(); document.getElementById('ms-bottom-sheet').classList.remove('open'); }
        // accordion toggles
        if(ev.target.classList && ev.target.classList.contains('ms-accordion-toggle')){ var t = ev.target.getAttribute('data-target'); var node = document.getElementById(t); if(node){ node.classList.toggle('open'); } }
      });
      // link-mode toggle (desktop + sheet)
      (function(){
        var lm = document.getElementById('ms-link-mode');
        var lms = document.getElementById('ms-link-mode-sheet');
        function updateLabel(){ if(LINK_MODE_JS === 'and'){ if(lm) lm.textContent = 'UND'; if(lms) lms.textContent = 'UND-Verknüpfung aktiv'; } else { if(lm) lm.textContent = 'ODER'; if(lms) lms.textContent = 'ODER-Verknüpfung aktiv'; } }
        function toggleMode(){ LINK_MODE_JS = (LINK_MODE_JS === 'and' ? 'or' : 'and'); updateLabel(); }
        if(lm) lm.addEventListener('click', toggleMode);
        if(lms) lms.addEventListener('click', toggleMode);
        updateLabel();
      })();
      // reset button
      document.addEventListener('click', function(ev){ if(ev.target && ev.target.id === 'ms-reset'){ document.querySelectorAll('.ms-filter-species, .ms-filter-status').forEach(function(el){ el.checked = true; }); var selectedSpecies = Object.keys(SPECIES_COLORS_JS); var selectedStatus = Object.keys(STATUS_INFO_JS); rebuildCluster(selectedSpecies, selectedStatus); } });
      // open/close bottom sheet via handle (swipe gestures minimal support)
      (function(){ var sheet = document.getElementById('ms-bottom-sheet'); var openBtn = document.getElementById('ms-open-sheet'); if(!sheet) return; document.getElementById('ms-control-toggle').addEventListener('click', function(){ var ctrl = document.getElementById('ms-control'); ctrl.classList.toggle('collapsed'); }); if(openBtn){ openBtn.addEventListener('click', function(){ sheet.classList.add('open'); }); }
        sheet.addEventListener('click', function(ev){ if(ev.target === sheet){ sheet.classList.remove('open'); } });
      })();
      // initial pass
      resolveMapAndCluster(function(map, cluster){ MS.map = map; MS.cluster = cluster; initMarkers(); });
      buildFilters();
      wireFilters();
      setTimeout(function(){ var selectedSpecies = Object.keys(SPECIES_COLORS_JS); var selectedStatus = Object.keys(STATUS_INFO_JS); rebuildCluster(selectedSpecies, selectedStatus); }, 250);
    })();
    </script>
    '''.replace('%SPECIES_COLORS_JSON%', json.dumps(SPECIES_COLORS, ensure_ascii=False))\
       .replace('%STATUS_INFO_JSON%', json.dumps(STATUS_INFO, ensure_ascii=False))


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
  if not species:
    return f"background:{NEUTRAL_FILL};"
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
  gradient_style = conic_gradient_for_species(species)
  status_color = STATUS_INFO[status_key]['color'] if status_key else '#9e9e9e'
  status_short = STATUS_INFO[status_key]['short'] if status_key else ''
  status_label = STATUS_INFO[status_key]['label'] if status_key else ''

  data_species = json.dumps(species, ensure_ascii=False)
  data_statuses = json.dumps(all_statuses, ensure_ascii=False)

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

  m = folium.Map(location=[52.5163, 13.3777], tiles='cartodbpositron', zoom_start=12)
  marker_cluster = plugins.MarkerCluster()
  m.add_child(marker_cluster)

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
    icon = folium.DivIcon(html=icon_html, icon_size=(26, 26), icon_anchor=(13, 13))

    tooltip_text = 'Mehrere Arten' if len(species) > 1 else (species[0] if species else 'Andere')
    folium.Marker(
      location=[latf, lonf],
      popup=folium.Popup(popup_html, max_width=450),
      tooltip=tooltip_text,
      icon=icon
    ).add_to(marker_cluster)
    count += 1

  m.get_root().html.add_child(folium.Element(controls_html))
  m.get_root().html.add_child(folium.Element('<div style="position: fixed; bottom: 0; left: 0; background: white; padding: 4px; z-index:9999">Markers: ' + str(count) + '</div>'))

  m.save(OUTPUT_HTML)
  conn.close()


if __name__ == '__main__':
  main()
