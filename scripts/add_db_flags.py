#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB = Path('brueter.sqlite')

def col_exists(cur, table, col):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())

def main():
    if not DB.exists():
        print('DB not found:', DB)
        return 2
    con = sqlite3.connect(str(DB))
    cur = con.cursor()
    changed = False
    if not col_exists(cur, 'gebaeudebrueter', 'noSpecies'):
        print('Adding column noSpecies')
        cur.execute("ALTER TABLE gebaeudebrueter ADD COLUMN noSpecies INTEGER DEFAULT 0")
        changed = True
    else:
        print('Column noSpecies already exists')
    if not col_exists(cur, 'gebaeudebrueter', 'is_test'):
        print('Adding column is_test')
        cur.execute("ALTER TABLE gebaeudebrueter ADD COLUMN is_test INTEGER DEFAULT 0")
        changed = True
    else:
        print('Column is_test already exists')

    # mark rows without species as noSpecies=1
    # assume species columns: mauersegler, sperling, schwalbe, star, fledermaus, andere
    try:
        cur.execute("UPDATE gebaeudebrueter SET noSpecies=1 WHERE (mauersegler IS NULL OR mauersegler=0) AND (sperling IS NULL OR sperling=0) AND (schwalbe IS NULL OR schwalbe=0) AND (star IS NULL OR star=0) AND (fledermaus IS NULL OR fledermaus=0) AND (andere IS NULL OR andere=0)")
        print('Set noSpecies for rows without species')
        changed = True
    except Exception as e:
        print('Warning: could not set noSpecies automatically:', e)

    # set is_test for web_id 1784 (id may exist)
    cur.execute('SELECT COUNT(*) FROM gebaeudebrueter WHERE web_id=1784')
    if cur.fetchone()[0] > 0:
        cur.execute('UPDATE gebaeudebrueter SET is_test=1 WHERE web_id=1784')
        print('Set is_test=1 for web_id 1784')
        changed = True
    else:
        print('web_id 1784 not present; skipping is_test assignment')

    if changed:
        con.commit()
        print('DB updated')
    else:
        print('No DB changes required')

    con.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
