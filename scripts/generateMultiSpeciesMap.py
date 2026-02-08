import sqlite3
from datetime import datetime
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
  # pseudo status for filtering rows where all status flags are 0
  'none': {'label': 'Ohne Status', 'color': '#9e9e9e', 'short': '—'},
}

# Priority order for primary status selection (first match wins)
STATUS_PRIORITY = ['verloren', 'sanierung', 'ersatz', 'kontrolle']

# Neutral fill for Status-only mode
NEUTRAL_FILL = '#cccccc'
# Controls and dynamic behavior (toggle modes + filters + hover)
controls_html = '''
    <style>
    .leaflet-container .ms-marker:hover { transform: scale(1.15); box-shadow: 0 1px 6px rgba(0,0,0,0.35); }
    /* Design tokens for ms-control (easy tuning) */
    :root {
      --ms-width: 380px;
      --ms-max-width-vw: 30vw;
      --ms-padding: 12px;
      --ms-gap: 12px;
      --ms-radius: 8px;
      --ms-bg: #ffffff;
      --ms-border: #e6e6e6;
      --ms-shadow: 0 6px 18px rgba(0,0,0,0.12);
      --ms-accent: #1976d2;
      --ms-focus: #2684ff;
    }
    /* Control box (desktop + mobile pinned top-right) */
    .ms-control {
      position: fixed;
      top: 10px;
      right: 10px;
      left: auto;
      background: var(--ms-bg);
      padding: var(--ms-padding);
      border: 1px solid var(--ms-border);
      border-radius: var(--ms-radius);
      z-index: 10002;
      box-shadow: var(--ms-shadow);
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      width: var(--ms-width);
      max-width: var(--ms-max-width-vw);
      max-height: 80vh;
      overflow: auto;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: var(--ms-gap);
    }
    /* collapsed: show only header (title + filter); keep header fully visible */
    .ms-control.collapsed { height: auto; overflow: visible; }
    .ms-control.collapsed .ms-row,
    .ms-control.collapsed .ms-section { display: none !important; }
    /* when collapsed hide the right-hand info toggle under Filter */
    .ms-control.collapsed .ms-right-header .ms-toggle { display: none !important; }
    .ms-control-header { display:flex; align-items:center; justify-content:space-between; gap:8px; position:sticky; top:0; background: var(--ms-bg); z-index:10003; padding-top:6px; padding-bottom:8px; border-bottom:1px solid rgba(0,0,0,0.06); width:100%; box-sizing:border-box; flex-shrink:0; }
    .ms-control h3 { margin: 0 0 6px 0; font-size: 15px; font-weight: 700; display:inline-block; }
    .ms-title-main { font-size: 15px; font-weight: 700; }
    .ms-title-sub { font-size: 12px; color: #555; margin-top: 2px; }
    .ms-top-header h3 { margin: 0; }
    .ms-top-header { display:flex; align-items:center; gap:8px; }
    .ms-right-header { display:flex; flex-direction:column; align-items:center; gap:6px; }
    .ms-collapse-btn { background: rgba(255,255,255,0.95); border: 1px solid rgba(0,0,0,0.06); font-size: 18px; padding: 8px; cursor: pointer; line-height: 1; position: absolute; top: 6px; right: 6px; z-index: 10010; touch-action: manipulation; -webkit-tap-highlight-color: transparent; pointer-events: auto; border-radius:6px; }
    .ms-open-sheet-btn { font-size:13px; padding:6px 8px; border-radius:6px; border:1px solid #ddd; background:#fff; cursor:pointer; }
    .ms-toggle { cursor: pointer; display: inline-flex; align-items: center; gap:8px; font-size:15px; color:#0b66c3; user-select: none; }
    .ms-toggle .arrow { display: none; }
    /* Filter button: blue border when control is expanded, transparent when collapsed */
    .ms-control:not(.collapsed) .ms-open-sheet-btn { border-color: var(--ms-accent); box-shadow: 0 6px 18px rgba(25,118,210,0.08); }
    .ms-control.collapsed .ms-open-sheet-btn { border-color: rgba(0,0,0,0.12); box-shadow: none; }
    .ms-control button, .ms-control .ms-open-sheet-btn, .ms-control .ms-toggle { transition: background .15s, box-shadow .12s, transform .08s; }
    .ms-control button:focus, .ms-control .ms-open-sheet-btn:focus, .ms-control .ms-toggle:focus { outline: 2px solid var(--ms-focus); outline-offset: 2px; }
    .ms-toggle .arrow { display:none !important; transition: transform .15s ease; }
    .ms-toggle.open .arrow { transform: rotate(90deg); }
    .ms-modal { position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.45); z-index:10000; display:flex; align-items:center; justify-content:center; }
    .ms-modal-content { background: #fff; padding: 18px 22px; border-radius:10px; max-width:700px; width:calc(100% - 40px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); position:relative; }
    .ms-modal-close { position:absolute; top:8px; right:8px; border:none; background:transparent; font-size:18px; cursor:pointer; }
    .ms-modal-body { font-size:14px; line-height:1.6; }
    .ms-modal-row { display:flex; gap:16px; align-items:flex-start; margin-top:4px; flex-wrap:wrap; }
    .ms-modal-text { flex:1 1 60%; font-size:15px; line-height:1.5; }
    .ms-modal-image { flex:1 1 30%; display:flex; align-items:flex-start; justify-content:flex-end; }
    .ms-modal-logo-lg { max-width:180px; max-height:120px; height:auto; width:auto; border-radius:6px; }
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
    .ms-section { background:#f7f7f7; border-radius:8px; padding:8px 10px; margin-top:8px; }
    .ms-row { display:flex; flex-wrap:wrap; gap:8px; align-items:flex-start; margin: 6px 0; }
    .ms-row label { font-size: 12px; line-height:1.5; display:flex; align-items:center; flex:0 0 calc(50% - 8px); box-sizing:border-box; }
    .ms-value { margin-left: 10px; font-size: 14px; color: #222; }
    /* custom neutral checkbox: no colored fill, dark-gray checkmark only */
    .ms-control input[type=checkbox] {
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      border: 1.5px solid rgba(0,0,0,0.35);
      border-radius: 4px;
      background: transparent;
      display: inline-block;
      vertical-align: middle;
      position: relative;
      box-sizing: border-box;
    }
    .ms-control input[type=checkbox]:focus {
      outline: 2px solid rgba(38,132,255,0.18);
      outline-offset: 2px;
    }
    .ms-control input[type=checkbox]:checked::after {
      content: '';
      position: absolute;
      left: 4px;
      top: 1px;
      width: 6px;
      height: 10px;
      border: solid #424242;
      border-width: 0 2px 2px 0;
      transform: rotate(45deg);
      box-sizing: content-box;
    }
    .ms-all-toggle { display:flex; align-items:center; gap:8px; flex:0 0 100%; margin-bottom:4px; }
    .ms-all-toggle input[type=checkbox] { position:absolute; opacity:0; width:0; height:0; }
    .ms-all-track { width:32px; height:16px; border-radius:999px; background:#ccc; position:relative; flex-shrink:0; transition: background .15s ease; }
    .ms-all-thumb { position:absolute; top:2px; left:2px; width:12px; height:12px; border-radius:50%; background:#fff; box-shadow:0 0 2px rgba(0,0,0,0.4); transition: transform .15s ease; }
    .ms-all-toggle input[type=checkbox]:checked + .ms-all-track { background:#1976d2; }
    .ms-all-toggle input[type=checkbox]:checked + .ms-all-track .ms-all-thumb { transform: translateX(16px); }
    /* small submit button next to help */
    .ms-submit-btn { font-size:13px; padding:6px 8px; border-radius:6px; border:1px solid #1976d2; background:#fff; cursor:pointer; color:#1976d2; }
    .ms-submit-btn:hover { background: #f5fbff; }
    .ms-submit-cta { display:inline-block; padding:6px 10px; border-radius:6px; border:1px solid #1976d2; background:#1976d2; color:#fff; text-decoration:none; }

    /* primary blue style for inline info button matching 'Filter anwenden' */
    .ms-info-btn { border: 1px solid var(--ms-accent); background: var(--ms-accent); color: #fff; box-shadow: 0 6px 18px rgba(25,118,210,0.08); }
    .ms-info-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(25,118,210,0.14); }
    .ms-info-btn span, .ms-info-btn small { color: #fff; }
    .ms-control button { min-height: 36px; }
    .ms-badge { display: none; }
    .ms-hidden { display: none !important; }

    /* Elegant button styles for filter controls */
    #ms-apply-desktop, #ms-apply-filters {
      font-size: 14px;
      padding: 8px 14px;
      border-radius: 10px;
      border: 1px solid transparent;
      background: var(--ms-accent);
      color: #fff;
      box-shadow: 0 4px 14px rgba(25,118,210,0.12);
      cursor: pointer;
      transition: transform .08s ease, box-shadow .12s ease, opacity .12s ease;
      min-width: 120px;
    }
    #ms-apply-desktop:hover, #ms-apply-filters:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(25,118,210,0.14); }
    #ms-reset {
      font-size: 13px;
      padding: 8px 12px;
      border-radius: 10px;
      background: transparent;
      color: var(--ms-accent);
      border: 1px solid rgba(25,118,210,0.14);
      cursor: pointer;
      transition: background .12s ease, transform .06s ease;
      min-width: 120px;
    }
    #ms-reset:hover { background: rgba(25,118,210,0.06); transform: translateY(-1px); }
    /* smaller submit CTA at bottom-right */
    #ms-submit-btn { padding: 8px 10px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.06); background: #fff; color: var(--ms-accent); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    #ms-submit-btn:hover { box-shadow: 0 6px 18px rgba(0,0,0,0.08); transform: translateY(-1px); }
    .leaflet-marker-icon.ms-div-icon {
      background: transparent !important;
      background-image: none !important;
      border: none !important;
      box-shadow: none !important;
      overflow: visible !important;
    }
    .leaflet-marker-icon.ms-div-icon::before,
    .leaflet-marker-icon.ms-div-icon::after { display: none !important; }
    /* subtle custom scrollbar for the control on desktop */
    .ms-control::-webkit-scrollbar { width: 8px; }
    .ms-control::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius:6px; }
    @media (max-width: 600px) {
      /* Pin control to top-right on mobile but show compact header and filter button */
      .ms-control { top: 10px; right: 10px; left: auto; bottom: auto; max-width: 92vw; border-radius: 10px; padding: 8px 10px; }
      .ms-control.collapsed { height: auto; overflow: visible; }
      .ms-control.collapsed .ms-row, .ms-control.collapsed .ms-section { display: none !important; }
      .ms-control .ms-toggle { display: none; }
      .ms-control .ms-reset-wrap { display: none; }
      .ms-open-sheet-btn { display:inline-block; }
      /* ensure bottom-sheet is above most elements */
      .ms-bottom-sheet { z-index: 10005; }
    }
    </style>
    <div class="ms-control collapsed" id="ms-control">
      <div class="ms-control-header" style="display:flex;justify-content:space-between;align-items:center;">
          <div class="ms-top-header" style="display:flex;align-items:center;gap:8px;">
            <div class="ms-title">
              <div class="ms-title-main">Karte der Gebäudebrüter in Berlin</div>
              <div class="ms-title-sub">Stand: %STAND_DATE%</div>
            </div>
          </div>
          <div class="ms-right-header" style="display:flex;flex-direction:column;align-items:center;gap:6px;">
            <button id="ms-open-sheet" class="ms-open-sheet-btn" title="Filter öffnen">Filter</button>
          </div>
        </div>
      <div class="desktop-only">
        <div class="ms-section">
          <h4>Filter Arten</h4>
          <div class="ms-row" id="ms-species-row"></div>
        </div>
        <div class="ms-section">
          <h4>Filter Status</h4>
          <div class="ms-row" id="ms-status-row"></div>
        </div>
        
        <div class="ms-row ms-reset-wrap" style="display:flex;justify-content:space-between;align-items:flex-end;">
          <div style="display:flex;flex-direction:column;align-items:flex-start;gap:6px;">
            <button id="ms-apply-desktop" title="Filter anwenden">Filter anwenden</button>
            <button id="ms-reset" title="Alle Marker zeigen">⟲ Filter zurücksetzen</button>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
            <div class="ms-more-info-copy-wrap" style="margin-bottom:4px;">
              <button id="ms-more-info-btn" class="ms-submit-btn ms-info-btn" title="Mehr Informationen anzeigen" aria-label="Mehr Informationen anzeigen" style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;">
                <span style="font-size:14px;line-height:1;color:#fff;">ⓘ</span>
                <span style="font-size:12px;color:#fff;">mehr Infos</span>
              </button>
            </div>
            <div style="display:flex;align-items:center;">
              <button id="ms-submit-btn" class="ms-submit-btn" title="Nistplatz melden">Nistplatz melden</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Bottom-sheet for mobile filters -->
    <div id="ms-bottom-sheet" class="ms-bottom-sheet" aria-hidden="true">
      <div class="ms-sheet-handle"></div>
      <div class="ms-sheet-header">
        <strong>Filter</strong>
        <button id="ms-more-info-toggle-sheet" class="ms-toggle" title="Mehr Informationen anzeigen" style="background:none;border:none;padding:0;cursor:pointer;"><span>ⓘ ?</span></button>
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
              <p>Diese Karte zeigt Standorte von Gebäudebrütern in Berlin. Gebäudebrüter sind Tiere wie Mauersegler, Schwalben, Sperlinge oder Fledermäuse, die an Gebäuden leben.</p>
              <p>Die Markierungen stehen für Häuser, an denen Gebäudebrüter gefunden und gemeldet wurden.</p>
	              <p style="margin-top:10px; font-size: 11px; color:#555;">Datenquelle: Online-Datenbank des Projekts Gebäudebrüter der NABU Bezirksgruppe Steglitz-Zehlendorf</p>
            </div>
            <div class="ms-modal-image">
              <img src="images/Logo%20BezGr%20SteglitzTempelhof%20farb%20(1).jpg" alt="Logo" class="ms-modal-logo-lg" />
            </div>
          </div>
          
          <h3 class="ms-modal-section-title">Tipps für die Nutzung der Karte</h3>
          <div class="ms-modal-text">
            <p>Setze Filter, um die angezeigten Arten und den Status von Nachweisen gezielt ein- oder auszublenden.</p>
            <p>Klicke in der Karte auf einen Standort-Marker, um weitere Informationen zu den dort erfassten Arten und Maßnahmen zu erhalten.</p>
          </div>
          
        </div>
      </div>
    </div>
    </div>
    <!-- Submit modal (triggered from control button) -->
    <div id="ms-submit-modal" class="ms-modal" style="display:none;">
      <div class="ms-modal-content">
        <button id="ms-submit-close" class="ms-modal-close" aria-label="Schließen">✕</button>
        <div class="ms-modal-body">
          <div class="ms-modal-text">
            <p><strong>Kennen Sie einen Nistplatz von Spatz, Schwalbe &amp; Co?</strong></p>
            <p>Dann freuen wir uns über Ihre Meldung! Je mehr Daten wir haben, desto besser können wir die Gebäudebrüter in Berlin schützen.</p>
            <div style="margin-top:12px; display:flex; gap:8px;">
              <a id="ms-submit-continue" href="https://berlin.nabu.de/wir-ueber-uns/bezirksgruppen/steglitz-zehlendorf/projekte/gebaeudebrueter/12400.html" target="_blank" rel="noopener" class="ms-submit-cta">Weiter zum Online-Formular</a>
              <button id="ms-submit-cancel" class="ms-submit-btn">Schließen</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <script>
    (function(){
      var SPECIES_COLORS_JS = %SPECIES_COLORS_JSON%;
      var STATUS_INFO_JS = %STATUS_INFO_JSON%;
      var ALL_SPECIES = Object.keys(SPECIES_COLORS_JS);
      var ALL_STATUS = Object.keys(STATUS_INFO_JS);
      // Cluster-aware filtering support (always AND across groups)
      var MS = { map:null, cluster:null, markers:[], ready:false };
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
      // More info modal toggle (desktop + mobile sheet)
      (function(){
        var togDesktop = document.getElementById('ms-more-info-toggle');
        var togSheet = document.getElementById('ms-more-info-toggle-sheet');
        var modal = document.getElementById('ms-info-modal');
        var closeBtn = document.getElementById('ms-info-close');
        var sheet = document.getElementById('ms-bottom-sheet');
        function openModal(ev){
          if(ev){ ev.preventDefault(); }
          if(sheet){ sheet.classList.remove('open'); }
          if(modal){ modal.style.display = 'flex'; }
        }
        function closeModal(){
          if(modal){ modal.style.display = 'none'; }
          if(sheet){ sheet.classList.remove('open'); }
        }
        if(togDesktop){ togDesktop.addEventListener('click', openModal); }
        if(togSheet){ togSheet.addEventListener('click', openModal); }
        // wire any copied desktop toggles or info buttons (e.g., placed near submit button)
        var extraDesktopTogs = document.querySelectorAll('.ms-more-info-toggle-copy, #ms-more-info-btn');
        extraDesktopTogs.forEach(function(t){ t.addEventListener('click', openModal); });
        if(closeBtn){ closeBtn.addEventListener('click', closeModal); }
        if(modal){ modal.addEventListener('click', function(ev){ if(ev.target === modal){ closeModal(); } }); }
      })();

      // Submit modal handlers (open submit modal from control button)
      (function(){
        var submitBtn = document.getElementById('ms-submit-btn');
        var submitModal = document.getElementById('ms-submit-modal');
        var submitClose = document.getElementById('ms-submit-close');
        var submitCancel = document.getElementById('ms-submit-cancel');
        var sheet = document.getElementById('ms-bottom-sheet');
        function openSubmit(ev){ if(ev){ ev.preventDefault(); } if(sheet){ sheet.classList.remove('open'); } if(submitModal){ submitModal.style.display = 'flex'; } }
        function closeSubmit(){ if(submitModal){ submitModal.style.display = 'none'; } }
        if(submitBtn){ submitBtn.addEventListener('click', openSubmit); }
        function isActuallyVisible(el){
          if(!el) return false;
          // getClientRects is empty when display:none or not in layout
          if(!el.getClientRects || el.getClientRects().length === 0) return false;
          var cs;
          try{ cs = window.getComputedStyle(el); }catch(e){ cs = null; }
          if(cs && (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0')) return false;
          return true;
        }
        function matchInfoButtonWidth(){
          var s = document.getElementById('ms-submit-btn');
          var i = document.getElementById('ms-more-info-btn');
          if(!isActuallyVisible(s) || !isActuallyVisible(i)) return false;
          var r = s.getBoundingClientRect();
          if(!r || r.width < 80) return false;
          i.style.width = Math.round(r.width) + 'px';
          i.style.minWidth = Math.round(r.width) + 'px';
          i.style.boxSizing = 'border-box';
          return true;
        }
        function matchApplyButtonWidth(){
          var reset = document.getElementById('ms-reset');
          var apply = document.getElementById('ms-apply-desktop');
          if(!isActuallyVisible(reset) || !isActuallyVisible(apply)) return false;
          var r = reset.getBoundingClientRect();
          if(!r || r.width < 120) return false;
          apply.style.width = Math.round(r.width) + 'px';
          apply.style.minWidth = Math.round(r.width) + 'px';
          apply.style.boxSizing = 'border-box';
          return true;
        }
        function scheduleButtonSizing(){
          // run over a few frames so layout/fonts settle
          var frames = 0;
          function tick(){
            frames++;
            matchApplyButtonWidth();
            matchInfoButtonWidth();
            if(frames < 6) requestAnimationFrame(tick);
          }
          requestAnimationFrame(tick);
        }
        // run once in case control starts expanded; otherwise we trigger on expand
        scheduleButtonSizing();
        window.addEventListener('resize', scheduleButtonSizing);
        if(submitClose){ submitClose.addEventListener('click', closeSubmit); }
        if(submitCancel){ submitCancel.addEventListener('click', closeSubmit); }
        if(submitModal){ submitModal.addEventListener('click', function(ev){ if(ev.target === submitModal){ closeSubmit(); } }); }
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
      function applyVisualsToMarker(m, selectedSpecies, selectedStatus, speciesAll, statusAll){
        var sp = m._ms.species || [];
        var st = m._ms.statuses || [];
        var spSel = speciesAll ? sp : (selectedSpecies.length ? intersection(sp, selectedSpecies) : []);
        var el = m._icon;
        var inner = el ? el.querySelector('.ms-marker') : null;
        if(inner){
          inner.style.background = computeGradient(spSel);
          var hasNoStatus = !st || st.length === 0;
          var wantsNoStatus = selectedStatus.indexOf('none') !== -1;
          var stSel = statusAll ? st : (selectedStatus.length ? intersection(st, selectedStatus) : []);
          var color = 'transparent';
          if(statusAll){
            color = m._ms.statusColor || '#9e9e9e';
          } else if(stSel.length){
            var key = stSel[0];
            color = (STATUS_INFO_JS[key] && STATUS_INFO_JS[key].color) || (m._ms.statusColor || '#9e9e9e');
          } else if(wantsNoStatus && hasNoStatus){
            color = (STATUS_INFO_JS['none'] && STATUS_INFO_JS['none'].color) || (m._ms.statusColor || '#9e9e9e');
          }
          inner.style.outline = '2px solid ' + color;
          var badge = inner.querySelector('.ms-badge'); if(badge){ badge.style.display = stSel.length ? 'block' : 'none'; badge.style.background = color; }
        }
      }
      function rebuildCluster(selectedSpecies, selectedStatus){
        if(!MS.ready){ return; }
        MS.cluster.clearLayers();
        var speciesAll = selectedSpecies.length === ALL_SPECIES.length;
        var statusAll = selectedStatus.length === ALL_STATUS.length;
        var toAdd = [];
        for(var i=0;i<MS.markers.length;i++){
          var m = MS.markers[i];
          var sp = m._ms.species || [];
          var st = m._ms.statuses || [];
          // Group semantics:
          // - none selected => show nothing
          // - all selected => do not restrict (also includes markers with empty st/sp)
          // - subset selected => restrict to intersection
          var speciesAllows = speciesAll ? true : (selectedSpecies.length ? intersection(sp, selectedSpecies).length > 0 : false);
          var hasNoStatus = !st || st.length === 0;
          var wantsNoStatus = selectedStatus.indexOf('none') !== -1;
          var statusAllows = statusAll ? true : (
            selectedStatus.length ? (
              (wantsNoStatus && hasNoStatus) || intersection(st, selectedStatus).length > 0
            ) : false
          );
          var visible = speciesAllows && statusAllows;
          if(visible){ toAdd.push(m); }
        }
        toAdd.forEach(function(m){ MS.cluster.addLayer(m); });
        setTimeout(function(){ MS.cluster.getLayers().forEach(function(m){ applyVisualsToMarker(m, selectedSpecies, selectedStatus, speciesAll, statusAll); }); }, 75);
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
        function makeAllCheckbox(id){
          var wrap = document.createElement('label');
          wrap.className = 'ms-all-toggle';
          var cb = document.createElement('input');
          cb.type = 'checkbox';
          cb.id = id;
          cb.checked = true;
          var track = document.createElement('span');
          track.className = 'ms-all-track';
          var thumb = document.createElement('span');
          thumb.className = 'ms-all-thumb';
          track.appendChild(thumb);
          var text = document.createElement('span');
          text.textContent = 'Alle';
          wrap.appendChild(cb);
          wrap.appendChild(track);
          wrap.appendChild(text);
          return {wrap: wrap, input: cb};
        }
        var sAllDesktop = makeAllCheckbox('ms-species-all'); sRow.appendChild(sAllDesktop.wrap);
        var sAllSheet = makeAllCheckbox('ms-species-all-sheet'); sAccordion.appendChild(sAllSheet.wrap);
        Object.keys(SPECIES_COLORS_JS).forEach(function(name){
          function makeEntry(prefix){
            var id = prefix + '-' + name;
            var wrap = document.createElement('label'); wrap.style.display = 'flex'; wrap.style.alignItems = 'center';
            var cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = name; cb.id = id; cb.className = 'ms-filter-species'; cb.checked = true;
              var swatch = document.createElement('span'); swatch.style.display = 'inline-block'; swatch.style.width = '12px'; swatch.style.height = '12px'; swatch.style.borderRadius = '50%'; swatch.style.margin = '0 0 0 6px'; swatch.style.background = SPECIES_COLORS_JS[name]; swatch.style.boxSizing = 'border-box';
            wrap.appendChild(cb);
            var value = document.createElement('span'); value.className = 'ms-value'; value.textContent = name;
            wrap.appendChild(value);
            wrap.appendChild(swatch);
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
            var swatch = document.createElement('span'); swatch.style.display = 'inline-block'; swatch.style.width = '12px'; swatch.style.height = '12px'; swatch.style.borderRadius = '50%'; swatch.style.margin = '0 0 0 6px'; swatch.style.background = 'transparent'; swatch.style.border = '2px solid ' + info.color; swatch.style.boxSizing = 'border-box';
            wrap.appendChild(cb);
            var value = document.createElement('span'); value.className = 'ms-value'; value.textContent = info.label;
            wrap.appendChild(value);
            wrap.appendChild(swatch);
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
       // wire controls (desktop: expand/collapse box via Filter, explicit 'Filter anwenden'; mobile: open sheet)
      document.addEventListener('click', function(ev){
        var openBtn = document.getElementById('ms-open-sheet');
        var sheet = document.getElementById('ms-bottom-sheet');
        var ctrl = document.getElementById('ms-control');
        // Filter button toggles desktop box or opens mobile sheet
        if(openBtn && ev.target === openBtn){
          if(window.innerWidth && window.innerWidth <= 600){
            if(sheet){ sheet.classList.add('open'); }
          } else {
            if(ctrl){
              ctrl.classList.toggle('collapsed');
              // after expanding, re-run sizing so widths are measured when visible
              if(!ctrl.classList.contains('collapsed')){
                try{ if(window.requestAnimationFrame){ requestAnimationFrame(function(){ requestAnimationFrame(function(){
                  var btn = document.getElementById('ms-submit-btn');
                  var info = document.getElementById('ms-more-info-btn');
                  var reset = document.getElementById('ms-reset');
                  var apply = document.getElementById('ms-apply-desktop');
                  if(btn && info){ var r1 = btn.getBoundingClientRect(); if(r1 && r1.width > 80){ info.style.width = Math.round(r1.width) + 'px'; info.style.minWidth = Math.round(r1.width) + 'px'; } }
                  if(reset && apply){ var r2 = reset.getBoundingClientRect(); if(r2 && r2.width > 120){ apply.style.width = Math.round(r2.width) + 'px'; apply.style.minWidth = Math.round(r2.width) + 'px'; } }
                }); }); } }catch(e){}
              }
            }
          }
        }
        // apply buttons
        if(ev.target && (ev.target.id === 'ms-apply-filters' || ev.target.id === 'ms-apply-desktop')){
          applyFilters();
          if(sheet && ev.target.id === 'ms-apply-filters'){ sheet.classList.remove('open'); }
        }
        // accordion toggles in bottom sheet
        if(ev.target && ev.target.classList && ev.target.classList.contains('ms-accordion-toggle')){
          var t = ev.target.getAttribute('data-target');
          var node = document.getElementById(t);
          if(node){ node.classList.toggle('open'); }
        }
      });
      // reset button
      document.addEventListener('click', function(ev){
        if(ev.target && ev.target.id === 'ms-reset'){
          // re-activate all species/status checkboxes
          document.querySelectorAll('.ms-filter-species, .ms-filter-status').forEach(function(el){ el.checked = true; });
          // re-activate "Alle" toggles in desktop + sheet
          document.querySelectorAll('#ms-species-all, #ms-species-all-sheet, #ms-status-all, #ms-status-all-sheet').forEach(function(el){ el.checked = true; });
          var selectedSpecies = Object.keys(SPECIES_COLORS_JS);
          var selectedStatus = Object.keys(STATUS_INFO_JS);
          rebuildCluster(selectedSpecies, selectedStatus);
        }
      });
      // close bottom sheet when tapping backdrop
      (function(){
        var sheet = document.getElementById('ms-bottom-sheet');
        if(!sheet) return;
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

  # determine last scraping date from DB (update_date)
  try:
    cur.execute("SELECT MAX(update_date) as last FROM gebaeudebrueter")
    last_raw = cur.fetchone()[0]
  except Exception:
    last_raw = None
  stand_text = ''
  if last_raw:
    try:
      # expect format 'YYYY-MM-DD HH:MM:SS' or similar
      dt = datetime.strptime(last_raw.split('.')[0], '%Y-%m-%d %H:%M:%S') if ' ' in last_raw else datetime.strptime(last_raw, '%Y-%m-%d')
      stand_text = f" - Stand: {dt.month:02d}.{dt.year}"
    except Exception:
      # fallback: try to extract year-month
      try:
        parts = last_raw.split('-')
        if len(parts) >= 2:
          stand_text = f" - Stand: {parts[1]}.{parts[0]}"
      except Exception:
        stand_text = ''

  m = folium.Map(location=[52.5163, 13.3777], tiles='cartodbpositron', zoom_start=12)
  marker_cluster = plugins.MarkerCluster()
  m.add_child(marker_cluster)

  query = (
    "SELECT b.web_id, b.bezirk, b.plz, b.ort, b.strasse, b.strasse_original, b.anhang, b.erstbeobachtung, b.beschreibung, b.besonderes, "
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
    # prefer Google coordinates when available, fall back to OSM
    if r['google_latitude'] is not None and str(r['google_latitude']) != 'None':
      lat = r['google_latitude']
      lon = r['google_longitude']
    elif r['osm_latitude'] is not None and str(r['osm_latitude']) != 'None':
      lat = r['osm_latitude']
      lon = r['osm_longitude']
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
    # prefer original street entry for display when present
    addr_field = r['strasse_original'] if (r['strasse_original'] and str(r['strasse_original']).strip()) else r['strasse']
    popup_html = (
      f"<b>Arten</b><br/>{fund_text}"
      f"<br/><br/><b>Status</b><br/>{status_text}"
      f"<br/><br/><b>Adresse</b><br/>{addr_field}, {r['plz']} {r['ort']}"
      f"<br/><br/><b>Erstbeobachtung</b><br/>{(str(r['erstbeobachtung']) if r['erstbeobachtung'] else 'unbekannt')}"
      f"<br/><br/><b>Beschreibung</b><br/>{(r['beschreibung'] or '')}"
      f"<br/><br/><b>Link zur Datenbank</b><br/><a href={url}?ID={r['web_id']}>{r['web_id']}</a>"
    )

    address_text = f"{addr_field}, {r['plz']} {r['ort']}"
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

  # prepare display date for title based on DB last update (use German month name)
  _stand_months = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']
  stand_display = ''
  if last_raw:
    try:
      dt = datetime.strptime(last_raw.split('.')[0], '%Y-%m-%d %H:%M:%S') if ' ' in last_raw else datetime.strptime(last_raw, '%Y-%m-%d')
      stand_display = f"{_stand_months[dt.month-1]} {dt.year}"
    except Exception:
      # fallback: try to extract year-month
      try:
        parts = last_raw.split('-')
        if len(parts) >= 2:
          stand_display = f"{parts[1]}.{parts[0]}"
      except Exception:
        stand_display = ''
  # replace placeholder in the control HTML and inject
  controls_with_stand = controls_html.replace('%STAND_DATE%', stand_display)
  m.get_root().html.add_child(folium.Element(controls_with_stand))
  m.get_root().html.add_child(folium.Element('<div style="position: fixed; bottom: 0; left: 0; background: white; padding: 4px; z-index:9999">Markers: ' + str(count) + '</div>'))

  m.save(OUTPUT_HTML)
  conn.close()


if __name__ == '__main__':
  main()
