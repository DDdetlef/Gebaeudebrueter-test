"""
Backup and remove inline original-street occurrences from `beschreibung`.

Usage:
  python scripts/clean_beschreibung_remove_original_inline.py --db=brueter.sqlite

Behavior:
  - Create a timestamped backup CSV of web_id, strasse, strasse_original, beschreibung in `reports/`.
  - For each row, if `beschreibung` contains any of:
      - exact `strasse_original` (when present) or exact `strasse` if original missing
      - variants of the note `(Originaleintrag_Straße)` or `(Originaleintrag Straße)`
    then remove those occurrences and normalize whitespace/punctuation.
  - Commit updates and print a summary with examples.
"""
import sqlite3
import os
import sys
import csv
import re
from datetime import datetime

DB = 'brueter.sqlite'
for a in sys.argv[1:]:
    if a.startswith('--db='):
        DB = a.split('=', 1)[1]
DB = os.environ.get('BRUETER_DB', DB)

OUT_DIR = 'reports'
os.makedirs(OUT_DIR, exist_ok=True)
now = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = os.path.join(OUT_DIR, f'backup_beschreibung_{now}.csv')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

rows = cur.execute('SELECT web_id, strasse, strasse_original, beschreibung FROM gebaeudebrueter').fetchall()

# write backup
with open(backup_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['web_id', 'strasse', 'strasse_original', 'beschreibung'])
    for r in rows:
        w.writerow([r['web_id'], r['strasse'] or '', r['strasse_original'] or '', (r['beschreibung'] or '').replace('\n', '\\n')])

# patterns
note_patterns = [
    re.compile(r"\(Originaleintrag[_\s]?Strae?e\)", re.IGNORECASE),
    re.compile(r"\(Originaleintrag[_\s]?Stra\.?\)", re.IGNORECASE),
    re.compile(r"Originaleintrag[_\s]?Strae?e", re.IGNORECASE),
]

updated = 0
examples = []

for r in rows:
    web_id = r['web_id']
    besch = r['beschreibung'] or ''
    original = (r['strasse_original'] or '').strip()
    fallback = (r['strasse'] or '').strip()
    target = original if original else fallback
    new = besch
    changed = False

    if not new:
        continue

    # remove any note patterns anywhere
    for p in note_patterns:
        if p.search(new):
            new = p.sub('', new)
            changed = True

    # remove exact target occurrences (word boundaries) if target non-empty
    if target:
        # escape for regex and match with word boundaries but allow some punctuation around
        esc = re.escape(target)
        # replace occurrences regardless of surrounding punctuation
        new2, nsub = re.subn(esc, '', new)
        if nsub > 0:
            new = new2
            changed = True

    if changed:
        # normalize repeated commas/spaces/newlines
        new = re.sub(r"\n{2,}", '\n', new)
        new = re.sub(r"[ ,;:\t]{2,}", ' ', new)
        new = new.strip()
        cur.execute('UPDATE gebaeudebrueter SET beschreibung = ? WHERE web_id = ?', (new, web_id))
        updated += 1
        if len(examples) < 10:
            examples.append((web_id, target, (besch or '')[:200], new[:200]))

conn.commit()
conn.close()

print(f'Backup written to {backup_path}')
print(f'Cleaned {updated} beschreibung entries. Examples:')
for e in examples:
    print(e)
