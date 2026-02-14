import re
from pathlib import Path

DOC = Path('docs') / 'GebaeudebrueterMultiMarkers.html'

def main():
    if not DOC.exists():
        print(f"Docs HTML not found: {DOC}")
        return
    text = DOC.read_text(encoding='utf-8')
    # count occurrences of var marker_ definitions
    markers_var = len(re.findall(r"\bvar\s+marker_[0-9a-f]+", text))
    markers_seticon = len(re.findall(r"marker_[0-9a-f]+\.setIcon\(", text))
    popup_defs = len(re.findall(r"var popup_[0-9a-f]+ =", text))
    html_defs = len(re.findall(r"var html_[0-9a-f]+ =", text))
    # count map markers by searching for L.marker( or L.markerClusterGroup addLayer markers
    lmarker_calls = len(re.findall(r"L\.marker\(|L\.circleMarker\(|L\.divIcon\(|L\.markerClusterGroup\(", text))
    # find the static 'Markers: ' label
    m_label = re.search(r"Markers:\s*(\d+)", text)
    print(f"file: {DOC}")
    print(f"var marker_ definitions: {markers_var}")
    print(f"marker.setIcon calls: {markers_seticon}")
    print(f"popup_ defs: {popup_defs}")
    print(f"html_ defs: {html_defs}")
    print(f"L.marker/L.divIcon/L.circleMarker/L.markerClusterGroup occurrences: {lmarker_calls}")
    if m_label:
        print(f"Static label found: Markers: {m_label.group(1)}")
        # show the surrounding lines
        idx = text.find(m_label.group(0))
        start = max(0, idx-200)
        end = min(len(text), idx+200)
        context = text[start:end]
        print('\nContext around label:')
        print(context.replace('\n',' '))
    else:
        print('No static Markers label found')

if __name__ == '__main__':
    main()
