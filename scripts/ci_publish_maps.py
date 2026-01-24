#!/usr/bin/env python3
import subprocess
import shutil
import sqlite3
import re
import sys
from pathlib import Path
import datetime

repo = Path.cwd()
tmp = repo / 'out' / 'tmp_maps'
db = repo / 'brueter.sqlite'

if tmp.exists():
    shutil.rmtree(tmp)
tmp.mkdir(parents=True)

if not db.exists():
    print('DB not found:', db)
    sys.exit(2)

shutil.copy(db, tmp / 'brueter.sqlite')

py = sys.executable
scripts = [repo / 'scripts' / 'long_lat_to_map_by_species.py', repo / 'scripts' / 'generateLocationMap.py']
for s in scripts:
    print('Running', s)
    res = subprocess.run([py, str(s)], cwd=str(tmp))
    if res.returncode != 0:
        print('Script failed:', s)
        sys.exit(res.returncode)

species = tmp / 'GebaeudebrueterBerlinBySpecies.html'
meldungen = tmp / 'GebaeudebrueterMeldungen.html'
if not species.exists() or not meldungen.exists():
    print('Expected HTML files not found in', tmp)
    sys.exit(3)

def extract_ids(path: Path):
    txt = path.read_text(encoding='utf-8', errors='ignore')
    ids = set(int(m) for m in re.findall(r'index\.php\?ID=(\d+)', txt))
    ids2 = set(int(m) for m in re.findall(r'>(\d{3,6})<', txt))
    return ids.union(ids2)

html_ids = extract_ids(species) | extract_ids(meldungen)

con = sqlite3.connect(str(tmp / 'brueter.sqlite'))
cur = con.cursor()
cur.execute('''
        SELECT DISTINCT g.web_id
        FROM gebaeudebrueter g
        LEFT JOIN geolocation_osm o ON g.web_id=o.web_id
        LEFT JOIN geolocation_google gg ON g.web_id=gg.web_id
        WHERE (o.web_id IS NOT NULL OR gg.web_id IS NOT NULL)
            AND (IFNULL(g.is_test,0)<>1)
            AND (IFNULL(g.noSpecies,0)<>1)
''')
geo_ids = set(r[0] for r in cur.fetchall())
con.close()

omitted = sorted(geo_ids - html_ids)
if omitted:
    out = repo / 'reports' / 'omitted_from_maps_ci.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        f.write('web_id\n')
        for w in omitted:
            f.write(str(w) + '\n')
    print(f'Omitted {len(omitted)} web_ids. Written {out}')
    sys.exit(4)

# All good — copy files into docs atomically (overwrite)
docs = repo / 'docs'
docs.mkdir(parents=True, exist_ok=True)
shutil.copy(species, docs / species.name)
shutil.copy(meldungen, docs / meldungen.name)

# Commit & push changes if any
def run(cmd, **kw):
    print('>', ' '.join(cmd))
    return subprocess.run(cmd, check=False, **kw)

run(['git', 'config', 'user.name', 'github-actions'])
run(['git', 'config', 'user.email', 'actions@github.com'])
run(['git', 'add', 'docs'])
diff = subprocess.run(['git', 'diff', '--staged', '--quiet'])
if diff.returncode != 0:
    msg = f'maps: regen {datetime.datetime.utcnow().isoformat()}'
    run(['git', 'commit', '-m', msg])
    run(['git', 'push', 'origin', 'HEAD:main'])
    print('Pushed updated docs')
else:
    print('No changes to commit')

print('Done')
