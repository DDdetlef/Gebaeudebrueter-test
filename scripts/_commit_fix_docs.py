import subprocess, sys

def run(cmd):
    print('> ' + ' '.join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.stdout:
        print(p.stdout)
    if p.stderr:
        print(p.stderr)
    return p.returncode

cmds = [
    ['git', 'add', 'scripts/generateMultiSpeciesMap.py', 'docs/GebaeudebrueterMultiMarkers.html'],
    ['git', 'commit', '-m', 'Sync docs HTML with regenerated map (header layout fix)']
]
for c in cmds:
    rc = run(c)
    if rc != 0:
        print('Command failed with exit code', rc)
        sys.exit(rc)
print('Done.')
