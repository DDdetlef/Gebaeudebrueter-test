import sqlite3
import sys
import os

DEFAULT_NABU = r"C:\Users\2andr\Documents\VisualStudioCode_Projekte\Gebaeudebrueter-test-master\Gebaeudebrueter-test\nabu_brueter.sqlite"

def ids(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id FROM gebaeudebrueter")
    s = set(r[0] for r in cur.fetchall())
    conn.close()
    return s

def count_table(db_path, table):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT count(*) FROM {table}")
        c = cur.fetchone()[0]
    except Exception:
        c = None
    conn.close()
    return c

def main():
    live = 'brueter.sqlite'
    nabu = sys.argv[1] if len(sys.argv)>1 else DEFAULT_NABU

    if not os.path.exists(nabu):
        print(f"NABU DB not found at: {nabu}")
        return
    if not os.path.exists(live):
        print(f"Live DB not found at: {live}")
        return

    print('Counts:')
    print(' live gebaeudebrueter =', count_table(live, 'gebaeudebrueter'))
    print(' nabu gebaeudebrueter =', count_table(nabu, 'gebaeudebrueter'))
    print(' live geolocation_google =', count_table(live, 'geolocation_google'))
    print(' nabu geolocation_google =', count_table(nabu, 'geolocation_google'))

    print('\nComparing IDs...')
    ids_live = ids(live)
    ids_nabu = ids(nabu)
    only_in_nabu = sorted(ids_nabu - ids_live)
    only_in_live = sorted(ids_live - ids_nabu)
    print('IDs only in NABU (count):', len(only_in_nabu))
    print('IDs only in LIVE (count):', len(only_in_live))
    if only_in_nabu:
        print('\nSample IDs only in NABU (first 20):')
        print(only_in_nabu[:20])
    if only_in_live:
        print('\nSample IDs only in LIVE (first 20):')
        print(only_in_live[:20])

    # optionally show one example full row from NABU for inspection
    if only_in_nabu:
        example = only_in_nabu[0]
        conn = sqlite3.connect(nabu)
        cur = conn.cursor()
        cur.execute('SELECT * FROM gebaeudebrueter WHERE id=?', (example,))
        row = cur.fetchone()
        conn.close()
        print(f"\nExample missing row from NABU (id={example}):")
        print(row)

if __name__ == '__main__':
    main()
