"""
Add missing street-original and flag columns to the `gebaeudebrueter` table.
Run before processing: `python scripts/add_street_flags_columns.py --db=brueter.sqlite`
"""
import sqlite3
import sys
import os

db_path = 'brueter.sqlite'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=', 1)[1]
        break
db_path = os.environ.get('BRUETER_DB', db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(gebaeudebrueter)")
cols = [r[1] for r in cur.fetchall()]

to_add = [
    ("strasse_original", "TEXT"),
    ("has_comma", "INTEGER DEFAULT 0"),
    ("has_slash", "INTEGER DEFAULT 0"),
    ("has_range", "INTEGER DEFAULT 0"),
    ("multiple_numbers", "INTEGER DEFAULT 0"),
    ("multiple_streets", "INTEGER DEFAULT 0"),
    ("kept_text_after_number", "INTEGER DEFAULT 0"),
]

for name, coldef in to_add:
    if name in cols:
        print(f"Column {name} already exists, skipping.")
        continue
    sql = f"ALTER TABLE gebaeudebrueter ADD COLUMN {name} {coldef}"
    try:
        cur.execute(sql)
        print(f"Added column {name}.")
    except Exception as e:
        print(f"Failed to add column {name}: {e}")

conn.commit()
conn.close()

print("Done. If you use migrations in other ways, integrate accordingly.")
