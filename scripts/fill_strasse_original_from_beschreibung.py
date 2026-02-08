"""
Fill `strasse_original` from `beschreibung` where missing.
Also recompute and write address flags for the original text.

Usage: python scripts/fill_strasse_original_from_beschreibung.py --db=brueter.sqlite
"""
import sqlite3
import os
import sys
import re

db_path = 'brueter.sqlite'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]
db_path = os.environ.get('BRUETER_DB', db_path)

try:
    from scripts.address_utils import _normalize_ws
except Exception:
    def _normalize_ws(s):
        return re.sub(r"\s+", " ", (s or '')).strip()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

q = "SELECT web_id, beschreibung, strasse_original, strasse FROM gebaeudebrueter"
rows = cur.execute(q).fetchall()

updated = 0
examples = []

street_kw = re.compile(r"\b(strasse|straße|str\.?|weg\b|allee\b|platz\b|gasse\b|ring\b|chaussee\b|ufer\b)\b", re.IGNORECASE)

for r in rows:
    web_id = r['web_id']
    so = r['strasse_original']
    beschr = r['beschreibung'] or ''
    if so and str(so).strip():
        continue
    # Look for the note in beschreibung
    m = re.match(r"\(Originaleintrag_Straße\)\s*(.+?)\s*(?:\r?\n|$)", beschr)
    if not m:
        continue
    orig_text = _normalize_ws(m.group(1))
    if not orig_text:
        continue

    # compute flags based on original text
    flags = {
        'has_comma': 1 if ',' in orig_text else 0,
        'has_slash': 1 if re.search(r'[;/|]', orig_text) else 0,
        'has_range': 1 if re.search(r'\d+\s*[-–/]\s*\d+', orig_text) else 0,
        'multiple_numbers': 0,
        'multiple_streets': 0,
        'flag_has_text_after_number': 0,
    }

    parts = re.split(r"[;/|]", orig_text)
    flags['multiple_streets'] = 1 if len(parts) > 1 else 0
    pick = None
    for p in parts:
        p2 = _normalize_ws(p)
        if re.search(r"\d", p2):
            pick = p2
            break
    if pick is None and parts:
        pick = _normalize_ws(parts[0])
    pick = pick or ''

    nums = re.findall(r"\d+", pick)
    flags['multiple_numbers'] = 1 if len(nums) > 1 else 0

    text_after = None
    m2 = re.search(r"^(.*?\D)?(\d+[A-Za-z]?)(.*)$", pick)
    if m2:
        rest = _normalize_ws(m2.group(3) or '')
        if rest and not street_kw.search(rest):
            flags['flag_has_text_after_number'] = 1
            text_after = rest

    # Update DB
    cur.execute(
        "UPDATE gebaeudebrueter SET strasse_original = ?, has_comma = ?, has_slash = ?, has_range = ?, multiple_numbers = ?, multiple_streets = ?, flag_has_text_after_number = ?, text_after_number = ? WHERE web_id = ?",
        (orig_text, flags['has_comma'], flags['has_slash'], flags['has_range'], flags['multiple_numbers'], flags['multiple_streets'], flags['flag_has_text_after_number'], text_after, web_id)
    )
    updated += 1
    if len(examples) < 10:
        examples.append((web_id, orig_text, flags))

conn.commit()
conn.close()

print(f'Updated {updated} rows by copying original from beschreibung into strasse_original')
for e in examples:
    print(e)
