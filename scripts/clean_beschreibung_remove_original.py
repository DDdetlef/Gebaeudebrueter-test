"""
Remove leading original-street notes from `beschreibung`.

Usage:
  python scripts/clean_beschreibung_remove_original.py --db=brueter.sqlite

Behavior:
  - For each row, if `beschreibung` starts with a line like
    "(Originaleintrag_Stratrae) ..." or variants, remove that leading line.
  - Also remove common variants like "(Originaleintrag Straße)" and leading whitespace after removal.
  - Commit changes and print a short report with examples.
"""
import sqlite3
import os
import sys
import re

DB = 'brueter.sqlite'
for a in sys.argv[1:]:
    if a.startswith('--db='):
        DB = a.split('=', 1)[1]
DB = os.environ.get('BRUETER_DB', DB)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# patterns for leading original-street notes (case-insensitive)
patterns = [
    re.compile(r"^\(Originaleintrag[_\s]?Strae?e\)\s*(.*)$", re.IGNORECASE),
    re.compile(r"^\(Originaleintrag[_\s]?Stra\.?\)\s*(.*)$", re.IGNORECASE),
    re.compile(r"^Originaleintrag[_\s]?Strae?e[:\s-]+(.*)$", re.IGNORECASE),
]

updated = 0
examples = []
cur.execute('SELECT web_id, beschreibung FROM gebaeudebrueter')
for web_id, beschreibung in cur.fetchall():
    if not beschreibung:
        continue
    orig = beschreibung
    lines = orig.splitlines()
    if not lines:
        continue
    first = lines[0].strip()
    matched = False
    for p in patterns:
        m = p.match(first)
        if m:
            # remove the first line; if the regex captured remainder, prepend it to next line
            rest_lines = lines[1:]
            captured = m.group(1).strip() if m.groups() else ''
            if captured:
                if rest_lines:
                    rest_lines[0] = captured + ('\n' + rest_lines[0] if rest_lines[0] else '')
                else:
                    rest_lines = [captured]
            # strip leading blank lines
            while rest_lines and (rest_lines[0].strip() == ''):
                rest_lines = rest_lines[1:]
            new = '\n'.join(rest_lines).lstrip()
            cur.execute('UPDATE gebaeudebrueter SET beschreibung = ? WHERE web_id = ?', (new, web_id))
            updated += 1
            if len(examples) < 10:
                examples.append((web_id, first, new[:200]))
            matched = True
            break
    # also handle explicit prefix "(Originaleintrag_Stratrae) " used elsewhere
    if not matched:
        note_prefix = '(Originaleintrag_Straße) '
        if orig.startswith(note_prefix):
            rest = '\n'.join(orig.splitlines(True)[1:])
            rest = rest.lstrip()
            cur.execute('UPDATE gebaeudebrueter SET beschreibung = ? WHERE web_id = ?', (rest, web_id))
            updated += 1
            if len(examples) < 10:
                examples.append((web_id, note_prefix.strip(), rest[:200]))

conn.commit()
conn.close()

print(f'Cleaned {updated} beschreibung entries. Examples:')
for e in examples:
    print(e)
