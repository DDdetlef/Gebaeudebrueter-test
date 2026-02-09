import sqlite3
import folium
from folium import plugins
from urllib.parse import quote

# Generate Meldungen map from database, prefer OSM coords then Google as fallback
try:
    conn = sqlite3.connect('brueter.sqlite')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
except Exception as e:
    raise

map1 = folium.Map(location=[52.5163,13.3777], tiles='cartodbpositron', zoom_start=12)

marker_cluster = plugins.MarkerCluster()
map1.add_child(marker_cluster)

query = ("SELECT b.web_id, b.bezirk, b.plz, b.ort, b.strasse, b.anhang, b.erstbeobachtung, b.beschreibung, b.besonderes, "
         "b.mauersegler, b.sperling, b.schwalbe, b.fledermaus, b.star, b.andere, "
         "o.latitude AS osm_latitude, o.longitude AS osm_longitude, gg.latitude AS google_latitude, gg.longitude AS google_longitude "
         "FROM gebaeudebrueter b "
         "LEFT JOIN geolocation_osm o ON b.web_id = o.web_id "
         "LEFT JOIN geolocation_google gg ON b.web_id = gg.web_id "
         "WHERE (b.is_test IS NULL OR b.is_test=0) AND (b.noSpecies IS NULL OR b.noSpecies=0)")

try:
    cur.execute(query)
except sqlite3.OperationalError:
    # fallback for older DB schema without is_test
    # fallback without schema-dependent filters/columns
    fallback_query = ("SELECT b.web_id, b.bezirk, b.plz, b.ort, b.strasse, b.anhang, b.erstbeobachtung, b.beschreibung, b.besonderes, "
                      "b.mauersegler, b.sperling, b.schwalbe, b.fledermaus, b.star, b.andere, "
                      "o.latitude AS osm_latitude, o.longitude AS osm_longitude, gg.latitude AS google_latitude, gg.longitude AS google_longitude "
                      "FROM gebaeudebrueter b "
                      "LEFT JOIN geolocation_osm o ON b.web_id = o.web_id "
                      "LEFT JOIN geolocation_google gg ON b.web_id = gg.web_id "
                      "WHERE 1=1")
    cur.execute(fallback_query)
rows = cur.fetchall()
url = 'http://www.gebaeudebrueter-in-berlin.de/index.php'
count = 0
for r in rows:
    web_id = r['web_id']
    # test rows are excluded via the SQL WHERE clause (is_test)
    # prefer osm, fallback to google
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

    # species classification: single vs multi; build list for popup
    species_flags = {
        'Mauersegler': bool(r['mauersegler']),
        'Sperling': bool(r['sperling']),
        'Schwalbe': bool(r['schwalbe']),
        'Fledermaus': bool(r['fledermaus']),
        'Star': bool(r['star']),
        'Andere': bool(r['andere'])
    }
    species_list = [name for name, flag in species_flags.items() if flag]
    color_map = {
        'Mauersegler': 'blue',
        'Sperling': 'green',
        'Schwalbe': 'purple',
        'Fledermaus': 'black',
        'Star': 'darkred',
        'Andere': 'orange'
    }
    fund = 'andere Art'
    tooltip_text = fund
    color = 'orange'
    if len(species_list) == 1:
        fund = species_list[0]
        tooltip_text = fund
        color = color_map.get(fund, 'orange')
    elif len(species_list) > 1:
        fund = ', '.join(species_list)
        tooltip_text = 'Mehrere Arten'
        color = 'cadetblue'

    popup_html = (
        f"<b>Fund</b><br/>{fund}"
        f"<br/><br/><b>Adresse</b><br/>{r['strasse']}, {r['plz']} {r['ort']}"
        f"<br/><br/><b>Erstbeobachtung</b><br/>{(str(r['erstbeobachtung']) if r['erstbeobachtung'] else 'unbekannt')}"
        f"<br/><br/><b>Beschreibung</b><br/>{(r['beschreibung'] or '')}"
        f"<br/><br/><b>Link zur Datenbank</b><br/><a href={url}?ID={web_id}>{web_id}</a>"
    )

    # add mailto button for reporting observations
    try:
        full_address = f"{r['strasse']}, {r['plz']} {r['ort']}".strip().strip(',')
        if not full_address or full_address.lower() == 'none':
            full_address = 'Adresse unbekannt'

        subject = f"Kontrolle Gebäudebrüter-Standort: Fundort-ID {web_id}"
        body = (
            "Hallo NABU-Team,\n\n"
            f"ich möchte folgende Beobachtung an der Adresse: {full_address}, Fundort-ID: {web_id} an den NABU melden.\n\n"
            "Beobachtete Vogelart(en):\n\n"
            "Anzahl der beobachteten Vögel:\n\n"
            "Nistplätze vorhanden: ja/nein\n\n"
            "Fotos im Anhang: ja/nein\n\n"
            "Eigene Beschreibung (mögliche Gefährdung):\n\n\n"
            "Mein Name:\n"
            "PLZ, Wohnort:\n"
            "Straße, Hausnummer:\n\n\n"
            "Viele Grüße,\n\n\n"
            "Hinweis zum Datenschutz: Der NABU erhebt und verarbeitet Ihre personenbezogenen Daten ausschließlich für Vereinszwecke. Dabei werden Ihre Daten - gegebenenfalls durch Beauftragte - auch für NABU-eigene Informationszwecke verarbeitet und genutzt. Eine Weitergabe an Dritte erfolgt niemals. Der Verwendung Ihrer Daten kann jederzeit schriftlich oder per E-Mail an lvberlin@nabu-berlin.de widersprochen werden.\n"
        )
        mailto = f"mailto:detlefdev@gmail.com?subject={quote(subject, safe='')}&body={quote(body, safe='')}"
        popup_html += (
            f"<br/><br/><a href=\"{mailto}\" target=\"_blank\" rel=\"noreferrer\" onclick=\"return gbHumanConfirmReport(event, {web_id}, this.href);\" "
            f"style=\"display:inline-block;padding:6px 10px;border-radius:6px;border:1px solid #1976d2;"
            f"background:#1976d2;color:#fff;text-decoration:none;\">Beobachtung melden</a>"
        )
    except Exception:
        pass

    folium.Marker(location=[latf, lonf], popup=folium.Popup(popup_html, max_width=450), tooltip=tooltip_text, icon=folium.Icon(color=color)).add_to(marker_cluster)
    count += 1

map1.get_root().html.add_child(folium.Element(
    '<style>'
    '.gb-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);display:none;align-items:center;justify-content:center;z-index:99999;}'
    '.gb-modal{background:#fff;border-radius:10px;max-width:420px;width:calc(100vw - 32px);box-shadow:0 10px 30px rgba(0,0,0,.25);padding:14px 16px;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;}'
    '.gb-modal h3{margin:0 0 8px 0;font-size:16px;}'
    '.gb-modal p{margin:0 0 10px 0;font-size:13px;line-height:1.35;color:#333;}'
    '.gb-modal label{display:block;font-size:12px;color:#333;margin:8px 0 4px;}'
    '.gb-modal input[type="text"], .gb-modal input[type="search"], .gb-modal input[type="email"], .gb-modal input[type="number"], .gb-modal textarea{width:100%;padding:8px 10px;border:1px solid #ccc;border-radius:8px;font-size:13px;}'
    '.gb-modal .gb-error{display:none;color:#b00020;font-size:12px;margin-top:6px;}'
    '.gb-modal .gb-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:12px;}'
    '.gb-modal button{border:0;border-radius:8px;padding:8px 10px;font-size:13px;cursor:pointer;}'
    '.gb-modal .gb-cancel{background:#eee;color:#333;}'
    '.gb-modal .gb-confirm{background:#1976d2;color:#fff;}'
    '</style>'
    '<div id="gbModalOverlay" class="gb-modal-overlay" role="dialog" aria-modal="true">'
    '  <div class="gb-modal">'
    '    <h3>Beobachtung melden</h3>'
    '    <p>Bitte bestätige zur Sicherheit die Fundort-ID, bevor dein E-Mail-Programm geöffnet wird.</p>'
    '    <div><b>Fundort-ID:</b> <span id="gbModalExpectedId">—</span></div>'
    '    <label for="gbModalInput">Fundort-ID eingeben</label>'
    '    <input id="gbModalInput" type="text" inputmode="numeric" autocomplete="off" />'
    '    <div style="margin-top:8px;"><label>Ich bin kein Bot <input id="gbModalCheckbox" type="checkbox" style="margin-left:8px;vertical-align:middle;" /></label></div>'
    '    <div id="gbModalError" class="gb-error">Fundort-ID stimmt nicht.</div>'
    '    <div class="gb-actions">'
    '      <button type="button" class="gb-cancel" onclick="gbModalClose()">Abbrechen</button>'
    '      <button id="gbModalConfirmBtn" type="button" class="gb-confirm" onclick="gbModalConfirm()" disabled>E-Mail öffnen</button>'
    '    </div>'
    '  </div>'
    '</div>'
    '<script>'
    'var gbModalState = { expectedId: null, href: null };'
    'function gbModalOpen(expectedId, href){'
    '  gbModalState.expectedId = String(expectedId);'
    '  gbModalState.href = href;'
    '  var ov = document.getElementById("gbModalOverlay");'
    '  document.getElementById("gbModalExpectedId").textContent = gbModalState.expectedId;'
    '  var inp = document.getElementById("gbModalInput");'
    '  inp.value = "";'
    '  var cb = document.getElementById("gbModalCheckbox"); if (cb) { cb.checked = false; }'
    '  var btn = document.getElementById("gbModalConfirmBtn"); if (btn) { btn.disabled = true; }'
    '  document.getElementById("gbModalError").style.display = "none";'
    '  ov.style.display = "flex";'
    '  setTimeout(function(){ inp.focus(); }, 0);'
    '}'
    'function gbModalClose(){'
    '  var ov = document.getElementById("gbModalOverlay");'
    '  ov.style.display = "none";'
    '  gbModalState.expectedId = null;'
    '  gbModalState.href = null;'
    '}'
    'function gbModalConfirm(){'
    '  var v = String(document.getElementById("gbModalInput").value || "").trim();'
    '  if (v !== gbModalState.expectedId){'
    '    document.getElementById("gbModalError").style.display = "block";'
    '    return;'
    '  }'
    '  var href = gbModalState.href;'
    '  gbModalClose();'
    '  try { window.location.href = href; } catch(e) { /* noop */ }'
    '}'
    'function gbHumanConfirmReport(evt, expectedId, href){'
    '  try { if (evt && evt.preventDefault) { evt.preventDefault(); } } catch(e) {}'
    '  gbModalOpen(expectedId, href);'
    '  return false;'
    '}'
    'try { document.getElementById("gbModalCheckbox").addEventListener("change", function(e){ try { document.getElementById("gbModalConfirmBtn").disabled = !this.checked; } catch(e){} }); } catch(e){}'
    'document.addEventListener("keydown", function(e){'
    '  var ov = document.getElementById("gbModalOverlay");'
    '  if (!ov || ov.style.display !== "flex") { return; }'
    '  if (e.key === "Escape") { gbModalClose(); }'
    '  if (e.key === "Enter") { gbModalConfirm(); }'
    '});'
    'document.addEventListener("click", function(e){'
    '  var ov = document.getElementById("gbModalOverlay");'
    '  if (ov && ov.style.display === "flex" && e.target === ov) { gbModalClose(); }'
    '});'
    '</script>'
))
map1.get_root().html.add_child(folium.Element('<div style="position: fixed; bottom: 0; left: 0; background: white; padding: 4px; z-index:9999">Markers: ' + str(count) + '</div>'))
map1.save('GebaeudebrueterMeldungen.html')
conn.close()
