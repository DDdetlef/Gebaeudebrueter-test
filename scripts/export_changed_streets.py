"""
Export rows where original street != cleaned street to CSV.
Usage: python scripts/export_changed_streets.py --db=brueter.sqlite --out=reports/changed_streets.csv
"""
import sqlite3
import os
import sys
import csv

db_path = 'brueter.sqlite'
out_path = 'reports/changed_streets.csv'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]
    elif arg.startswith('--out='):
        out_path = arg.split('=',1)[1]

db_path = os.environ.get('BRUETER_DB', db_path)

os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# determine available columns
cur.execute("PRAGMA table_info(gebaeudebrueter)")
cols_info = cur.fetchall()
cols = [c[1] for c in cols_info]

optional_flags = [
    'has_comma', 'has_slash', 'has_range', 'multiple_numbers',
    'multiple_streets', 'kept_text_after_number', 'strasse_original'
]

select_cols = ['web_id', 'strasse_original', 'strasse AS cleaned_strasse', 'plz', 'ort', 'beschreibung']
for f in optional_flags:
    if f in cols and f not in [c.split()[0] for c in select_cols]:
        select_cols.append(f)

select_sql = ', '.join(select_cols)

query = f"SELECT {select_sql} FROM gebaeudebrueter WHERE COALESCE(trim(strasse_original), '') != COALESCE(trim(strasse), '')"
cur.execute(query)
rows = cur.fetchall()

with open(out_path, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.writer(fh)
    writer.writerow(rows[0].keys() if rows else [c.split(' AS ')[-1] for c in select_cols])
    for r in rows:
        writer.writerow([r[c.split(' AS ')[-1]] if (' AS ' in c and c.split(' AS ')[-1] in r.keys()) else r[c] for c in select_cols])

print(f'Wrote {len(rows)} rows to {out_path}')
conn.close()
