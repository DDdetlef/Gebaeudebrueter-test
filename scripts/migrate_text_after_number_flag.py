"""
Add `flag_has_text_after_number` and `text_after_number` columns and populate them.
Attempt to drop obsolete column `kept_text_after_number` (if SQLite supports it).

Run: python scripts/migrate_text_after_number_flag.py --db=brueter.sqlite
"""
import sqlite3
import sys
import os
import re

db_path = 'brueter.sqlite'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]
db_path = os.environ.get('BRUETER_DB', db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Add columns if missing
cols = [c[1] for c in cur.execute("PRAGMA table_info(gebaeudebrueter)").fetchall()]
if 'flag_has_text_after_number' not in cols:
    cur.execute("ALTER TABLE gebaeudebrueter ADD COLUMN flag_has_text_after_number INTEGER DEFAULT 0")
    print('Added column flag_has_text_after_number')
else:
    print('Column flag_has_text_after_number already exists')

if 'text_after_number' not in cols:
    cur.execute("ALTER TABLE gebaeudebrueter ADD COLUMN text_after_number TEXT")
    print('Added column text_after_number')
else:
    print('Column text_after_number already exists')

conn.commit()

# Prepare patterns similar to address_utils
def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or '')).strip()

street_kw = re.compile(r"\b(strasse|straße|str\.?|weg\b|allee\b|platz\b|gasse\b|ring\b|chaussee\b|ufer\b)\b", re.IGNORECASE)

updated = 0
checked = 0
def _rest_is_house_suffix(text: str) -> bool:
    t = (text or '').strip()
    if not t:
        return False
    return bool(re.match(r"^[\s,]*[+\-]?[A-Za-z](?:\s*[-–]\s*[A-Za-z])?(?:\s*(?:,|\s)\s*[+\-]?[A-Za-z](?:\s*[-–]\s*[A-Za-z])?)*[\s,]*$", t))


for web_id, orig, s in cur.execute('SELECT web_id, strasse_original, strasse FROM gebaeudebrueter'):
    checked += 1
    db_orig = (orig or '').strip()
    db_str = (s or '').strip()
    original_used = db_orig if db_orig else db_str
    pick = _normalize_ws(original_used)
    # split on street separators and pick the part containing a digit if present
    parts = re.split(r"[;/|]", pick)
    chosen = None
    for p in parts:
        if re.search(r"\d", p):
            chosen = _normalize_ws(p)
            break
    if chosen is None and parts:
        chosen = _normalize_ws(parts[0])
    if not chosen:
        # nothing to do
        continue
    m = re.search(r"^(.*?\D)?(\d+[A-Za-z]?)(.*)$", chosen)
    text_after = None
    has_text_after = 0
    if m:
        rest = _normalize_ws(m.group(3) or '')
        # If rest begins with a numeric range like '-13' or '/13', treat as range
        range_match = re.match(r"^\s*[-–/]\s*\d+", rest)
        has_range_db = 1 if range_match else 0
        # consider it text after number only if non-empty, NOT a second street, NOT a house-suffix pattern, and not containing digits
        if rest and not street_kw.search(rest) and not _rest_is_house_suffix(rest) and not re.search(r"\d", rest):
            text_after = rest
            has_text_after = 1
        else:
            has_text_after = 0
    # always write flag/text (clear when not present)
    # update text_after_number and flag_has_text_after_number; if we detected a range, set has_range
    if 'has_range_db' in locals() and has_range_db:
        cur.execute('UPDATE gebaeudebrueter SET flag_has_text_after_number = ?, text_after_number = ?, has_range = 1 WHERE web_id = ?', (has_text_after, text_after, web_id))
    else:
        cur.execute('UPDATE gebaeudebrueter SET flag_has_text_after_number = ?, text_after_number = ? WHERE web_id = ?', (has_text_after, text_after, web_id))
    if has_text_after:
        updated += 1

conn.commit()

print(f'Checked {checked} rows, updated {updated} rows with text after number.')

# Attempt to drop obsolete column kept_text_after_number
cols = [c[1] for c in cur.execute("PRAGMA table_info(gebaeudebrueter)").fetchall()]
if 'kept_text_after_number' in cols:
    try:
        cur.execute('ALTER TABLE gebaeudebrueter DROP COLUMN kept_text_after_number')
        conn.commit()
        print('Dropped column kept_text_after_number')
    except sqlite3.OperationalError as e:
        print('Could not drop column kept_text_after_number (SQLite may not support DROP COLUMN). Setting values to NULL instead.')
        try:
            cur.execute('UPDATE gebaeudebrueter SET kept_text_after_number = NULL')
            conn.commit()
            print('Cleared values in kept_text_after_number')
        except Exception as e2:
            print('Failed to clear kept_text_after_number:', e2)
else:
    print('No column kept_text_after_number present')

conn.close()
