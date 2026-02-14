import sqlite3
import sys
import os

def load_ids(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute('SELECT DISTINCT web_id FROM gebaeudebrueter WHERE web_id IS NOT NULL')
    except Exception as e:
        print('ERROR reading', db_path, e)
        return set()
    rows = cur.fetchall()
    ids = set()
    for (w,) in rows:
        try:
            ids.add(int(w))
        except:
            pass
    conn.close()
    return ids


def main():
    if len(sys.argv) < 3:
        print('Usage: compare_databases.py <db_a> <db_b>')
        sys.exit(1)
    a = sys.argv[1]
    b = sys.argv[2]
    out_dir = 'reports'
    os.makedirs(out_dir, exist_ok=True)

    ids_a = load_ids(a)
    ids_b = load_ids(b)

    new_ids = sorted(list(ids_a - ids_b))
    common = len(ids_a & ids_b)

    out_file = os.path.join(out_dir, 'new_webids_vs_otherdb.txt')
    with open(out_file, 'w', encoding='utf-8') as fh:
        fh.write('# db_a: %s\n' % a)
        fh.write('# db_b: %s\n' % b)
        fh.write('total_in_a=%d\n' % len(ids_a))
        fh.write('total_in_b=%d\n' % len(ids_b))
        fh.write('common=%d\n' % common)
        fh.write('new_in_a=%d\n' % len(new_ids))
        for i in new_ids:
            fh.write(str(i) + '\n')

    print('a=', a)
    print('b=', b)
    print('total_in_a=', len(ids_a))
    print('total_in_b=', len(ids_b))
    print('common=', common)
    print('new_in_a=', len(new_ids))
    print('wrote=', out_file)


if __name__ == '__main__':
    main()
