"""
Apply cleaned street values (from `sanitize_street`) into `gebaeudebrueter.strasse`.
Usage: python scripts/apply_cleaned_streets.py --db=brueter.sqlite

This updates only when cleaned != current `strasse` and cleaned is non-empty.
It preserves `strasse_original`.
"""
import sqlite3
import os
import sys

db_path = 'brueter.sqlite'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]
db_path = os.environ.get('BRUETER_DB', db_path)

try:
    from scripts.address_utils import sanitize_street
except Exception:
    try:
        from address_utils import sanitize_street
    except Exception as e:
        raise RuntimeError('Cannot import sanitize_street from scripts/address_utils.py') from e

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT web_id, strasse_original, strasse FROM gebaeudebrueter')
rows = cur.fetchall()

updated = 0
examples = []
for r in rows:
    web_id = r['web_id']
    db_orig = (r['strasse_original'] or '').strip()
    db_str = (r['strasse'] or '').strip()
    original_used = db_orig if db_orig else db_str
    cleaned, flags, _ = sanitize_street(original_used or '')
    cleaned = (cleaned or '').strip()
    if cleaned and cleaned != db_str:
        cur.execute('UPDATE gebaeudebrueter SET strasse = ? WHERE web_id = ?', (cleaned, web_id))
        updated += 1
        if len(examples) < 10:
            examples.append((web_id, db_str, cleaned))

conn.commit()
conn.close()

print(f'Updated {updated} rows in gebaeudebrueter.strasse')
if examples:
    print('Examples (web_id, old, new):')
    for e in examples:
        print(e)
