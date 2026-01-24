import re
from pathlib import Path

species = Path('docs') / 'GebaeudebrueterBerlinBySpecies.html'
meldungen = Path('docs') / 'GebaeudebrueterMeldungen.html'

def extract(path):
    txt = path.read_text(encoding='utf-8', errors='ignore')
    ids = set(int(m) for m in re.findall(r'index\.php\?ID=(\d+)', txt))
    ids2 = set(int(m) for m in re.findall(r'>(\d{3,6})<', txt))
    return ids.union(ids2)

ids_s = extract(species)
ids_m = extract(meldungen)
all_ids = ids_s.union(ids_m)
print('species_count', len(ids_s), 'meldungen_count', len(ids_m), 'union', len(all_ids))
txt_s = (species.read_text(encoding='utf-8', errors='ignore'))
txt_m = (meldungen.read_text(encoding='utf-8', errors='ignore'))
print('species L.marker count', txt_s.count('L.marker('), 'meldungen L.marker count', txt_m.count('L.marker('))
print('species var marker count', txt_s.count('var marker_'), 'meldungen var marker count', txt_m.count('var marker_'))
for sample in [385,1784,1214,1680]:
    print(sample, 'in species?', sample in ids_s, 'in meldungen?', sample in ids_m, 'in union?', sample in all_ids)
