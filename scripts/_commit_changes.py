import subprocess
import sys
from pathlib import Path
import shutil


def run(cmd):
    print('> ' + ' '.join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.stdout:
        print(p.stdout)
    if p.stderr:
        print(p.stderr)
    return p.returncode


def ensure_docs_copy(src='GebaeudebrueterMultiMarkers.html', dst_dir='docs'):
    src_p = Path(src)
    dst_dir_p = Path(dst_dir)
    dst_dir_p.mkdir(parents=True, exist_ok=True)
    dst_p = dst_dir_p / src_p.name
    if not src_p.exists():
        print(f"Source file {src} not found; skipping docs copy")
        return False
    try:
        shutil.copy2(src_p, dst_p)
        print(f"Copied {src} -> {dst_p}")
        return True
    except Exception as e:
        print('Copy failed:', e)
        return False


if __name__ == '__main__':
    copied = ensure_docs_copy()
    cmds = []
    # Always add the generator script if present
    cmds.append(['git', 'add', 'scripts/generateMultiSpeciesMap.py'])
    if copied:
        cmds.append(['git', 'add', 'docs/GebaeudebrueterMultiMarkers.html'])
    cmds.append(['git', 'commit', '-m', 'UI: compact collapsed control — hide second row; regenerate docs HTML'])

    for c in cmds:
        rc = run(c)
        if rc != 0:
            print('Command failed with exit code', rc)
            sys.exit(rc)
    print('Done.')
