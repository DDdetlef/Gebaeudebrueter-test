"""
Prepend original street note to `beschreibung` when cleaned street differs.

Usage:
  python scripts/prepend_original_street_to_beschreibung.py --db=brueter.sqlite

Behavior:
  - For each row in `gebaeudebrueter` determine `original_used` = `strasse_original` if present else `strasse`.
  - Compute `cleaned` via `sanitize_street(original_used)` from `scripts/address_utils.py`.
  - If `original_used.strip()` != `cleaned.strip()` and the `beschreibung` does not already start with the note,
    update `beschreibung` to: "(Originaleintrag_Straße) <original_used>\n<old_beschreibung>".
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

cur.execute('SELECT web_id, strasse_original, strasse, beschreibung FROM gebaeudebrueter')
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
    orig_used_norm = (original_used or '').strip()
    beschreibung = r['beschreibung'] or ''

    if not orig_used_norm:
        continue

    if orig_used_norm != cleaned:
        # If strasse_original is empty, copy original_used there (do not move into beschreibung)
        cur.execute('SELECT strasse_original FROM gebaeudebrueter WHERE web_id = ?', (web_id,))
        cur_so = cur.fetchone()[0]
        if not cur_so or not str(cur_so).strip():
            cur.execute('UPDATE gebaeudebrueter SET strasse_original = ? WHERE web_id = ?', (orig_used_norm, web_id))

        # Remove any existing leading "(Originaleintrag_Straße) ..." note from beschreibung
        note_prefix = '(Originaleintrag_Straße) '
        if beschreibung.startswith(note_prefix):
            # remove first line
            rest_lines = beschreibung.splitlines(True)[1:]
            new_beschr = ''.join(rest_lines)
            cur.execute('UPDATE gebaeudebrueter SET beschreibung = ? WHERE web_id = ?', (new_beschr, web_id))

        updated += 1
        if len(examples) < 10:
            examples.append((web_id, orig_used_norm, cleaned))

conn.commit()
conn.close()

print(f'Updated {updated} rows. Examples:')
for e in examples:
    print(e)
