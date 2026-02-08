"""
Inspect `gebaeudebrueter` table for street/original/flag columns and sample rows.
Usage: python scripts/inspect_db_for_streets.py --db=brueter.sqlite
"""
import sqlite3
import sys
import os

db='brueter.sqlite'
for a in sys.argv[1:]:
    if a.startswith('--db='):
        db=a.split('=',1)[1]
db=os.environ.get('BRUETER_DB', db)

conn=sqlite3.connect(db)
cur=conn.cursor()

print('PRAGMA table_info(gebaeudebrueter):')
cols_info = cur.execute("PRAGMA table_info(gebaeudebrueter)").fetchall()
for r in cols_info:
    print(r)

cols=[c[1] for c in cols_info]

print('\nDetected columns count:', len(cols))

flags = [f for f in ['has_comma','has_slash','has_range','multiple_numbers','multiple_streets','kept_text_after_number'] if f in cols]
print('\nFlag columns present:', flags)

orig_cols = [c for c in ['strasse_original','strasse_original_text','strasse_orig','strasse_orig_text'] if c in cols]
print('Possible original columns found:', orig_cols)

clean_candidates = [c for c in ['strasse','strasse_clean','strasse_bereinigt','strasse_cleaned'] if c in cols]
print('Possible cleaned columns found:', clean_candidates)

print('\nCounting non-empty original columns (if present):')
for c in orig_cols:
    cnt = cur.execute(f"SELECT COUNT(*) FROM gebaeudebrueter WHERE {c} IS NOT NULL AND trim({c})!=''").fetchone()[0]
    print(f"  {c}: {cnt}")

if 'strasse' in cols:
    cnt2 = cur.execute("SELECT COUNT(*) FROM gebaeudebrueter WHERE strasse IS NOT NULL AND trim(strasse)!=''").fetchone()[0]
    print('\nNon-empty `strasse` count:', cnt2)

print('\nSample rows where strasse_original IS NOT NULL or strasse contains a comma (up to 10):')
query = "SELECT web_id, strasse, strasse_original" if 'strasse_original' in cols else "SELECT web_id, strasse"
query += " FROM gebaeudebrueter WHERE (strasse_original IS NOT NULL AND trim(strasse_original)!='') OR strasse LIKE '%,%' LIMIT 10"
try:
    for r in cur.execute(query).fetchall():
        print(r)
except Exception as e:
    print('Query failed:', e)

conn.close()
