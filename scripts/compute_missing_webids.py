import sqlite3
import os


EXPECTED_MAX = 2588
DB_PATH = 'brueter.sqlite'
OUT_PATH = os.path.join('reports', 'missing_webids.txt')


def main():
    os.makedirs('reports', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT web_id FROM gebaeudebrueter WHERE web_id IS NOT NULL')
    rows = cur.fetchall()
    present = set()
    for (w,) in rows:
        try:
            present.add(int(w))
        except:
            pass

    missing = [i for i in range(1, EXPECTED_MAX + 1) if i not in present]

    with open(OUT_PATH, 'w', encoding='utf-8') as fh:
        for i in missing:
            fh.write(str(i) + '\n')

    print(f'Present: {len(present)}, Missing: {len(missing)}. Written to {OUT_PATH}')
    conn.close()


if __name__ == '__main__':
    main()
