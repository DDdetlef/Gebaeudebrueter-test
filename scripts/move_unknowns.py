import sqlite3
import shutil
import os

SRC_DB = 'brueter.sqlite'
DEST_DB = 'noSpecies.sqlite'
BACKUP = 'brueter.sqlite.bak'

def main():
    if not os.path.exists(SRC_DB):
        print('Source DB not found:', SRC_DB)
        return
    # backup
    shutil.copy2(SRC_DB, BACKUP)
    print('Backup created:', BACKUP)

    src = sqlite3.connect(SRC_DB)
    src.row_factory = sqlite3.Row
    s_cur = src.cursor()

    # detect species columns
    s_cur.execute("PRAGMA table_info(gebaeudebrueter)")
    cols = [r[1] for r in s_cur.fetchall()]
    species_cols = [c for c in ['sperling','mauersegler','schwalbe','star','fledermaus','andere'] if c in cols]
    if not species_cols:
        print('No species flag columns found; nothing to move.')
        return

    expr = ' + '.join([f"COALESCE({c},0)" for c in species_cols])
    q = f"SELECT rowid, * FROM gebaeudebrueter WHERE ({expr})=0 ORDER BY rowid"
    s_cur.execute(q)
    rows = s_cur.fetchall()
    if not rows:
        print('No unknown-species rows found; nothing to do.')
        return

    # prepare destination DB and create table if missing
    dest_exists = os.path.exists(DEST_DB)
    dest = sqlite3.connect(DEST_DB)
    d_cur = dest.cursor()

    if not dest_exists:
        # get CREATE TABLE SQL from source
        s_cur2 = src.cursor()
        s_cur2.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='gebaeudebrueter'")
        row = s_cur2.fetchone()
        if not row or not row[0]:
            print('Could not obtain CREATE TABLE for gebaeudebrueter')
            return
        create_sql = row[0]
        d_cur.execute(create_sql)
        dest.commit()
        print('Created table gebaeudebrueter in', DEST_DB)
    else:
        # ensure table exists
        d_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gebaeudebrueter'")
        if not d_cur.fetchone():
            s_cur2 = src.cursor()
            s_cur2.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='gebaeudebrueter'")
            row = s_cur2.fetchone()
            if row and row[0]:
                d_cur.execute(row[0])
                dest.commit()
                print('Created missing table in', DEST_DB)

    # insert rows into dest
    # determine column names (exclude the implicit rowid from SELECT * mapping)
    s_cur.execute('PRAGMA table_info(gebaeudebrueter)')
    table_cols = [r[1] for r in s_cur.fetchall()]
    insert_cols = table_cols
    placeholders = ','.join(['?'] * len(insert_cols))
    insert_sql = f"INSERT INTO gebaeudebrueter ({', '.join(insert_cols)}) VALUES ({placeholders})"

    moved = 0
    web_ids = []
    for r in rows:
        # r[0] is rowid, r[1:] correspond to table_cols in order
        vals = list(r)[1:]
        d_cur.execute(insert_sql, vals)
        moved += 1
        # get web_id if present
        try:
            web_ids.append(r['web_id'])
        except Exception:
            pass

    dest.commit()
    print(f'Moved {moved} rows to {DEST_DB}')

    # delete from source by web_id if available, otherwise by rowid
    if web_ids:
        # delete in chunks
        chunk = 200
        for i in range(0, len(web_ids), chunk):
            chunk_ids = web_ids[i:i+chunk]
            placeholders = ','.join(['?'] * len(chunk_ids))
            s_cur.execute(f"DELETE FROM gebaeudebrueter WHERE web_id IN ({placeholders})", chunk_ids)
    else:
        # fallback: delete by rowid range gathered earlier
        rowids = [r[0] for r in rows]
        chunk = 200
        for i in range(0, len(rowids), chunk):
            chunk_ids = rowids[i:i+chunk]
            placeholders = ','.join(['?'] * len(chunk_ids))
            s_cur.execute(f"DELETE FROM gebaeudebrueter WHERE rowid IN ({placeholders})", chunk_ids)

    src.commit()
    print('Deleted moved rows from', SRC_DB)

    src.close()
    dest.close()

if __name__ == '__main__':
    main()
