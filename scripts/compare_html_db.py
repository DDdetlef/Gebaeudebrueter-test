import re
import sqlite3
from pathlib import Path

HTML = Path('docs') / 'GebaeudebrueterMultiMarkers.html'
DB = 'brueter.sqlite'


def ids_in_html(path):
    text = path.read_text(encoding='utf-8')
    ids = set(map(int, re.findall(r"[?&]ID=(\d+)", text)))
    # also find plain numeric anchors like >2442< as fallback for some entries
    if not ids:
        ids = set(map(int, re.findall(r">(\d{2,5})<", text)))
    return ids


def ids_in_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id FROM gebaeudebrueter")
    s = set(r[0] for r in cur.fetchall())
    conn.close()
    return s


def main():
    if not HTML.exists():
        print(f"HTML file not found: {HTML}")
        return
    if not Path(DB).exists():
        print(f"DB file not found: {DB}")
        return

    html_ids = ids_in_html(HTML)
    db_ids = ids_in_db(DB)

    print(f"HTML marker count (unique IDs found): {len(html_ids)}")
    print(f"DB marker count: {len(db_ids)}")

    only_in_html = sorted(html_ids - db_ids)
    only_in_db = sorted(db_ids - html_ids)

    print(f"IDs only in HTML: {len(only_in_html)}")
    print(f"IDs only in DB: {len(only_in_db)}")

    if only_in_html:
        print('\nSample IDs only in HTML (first 50):')
        print(only_in_html[:50])
    if only_in_db:
        print('\nSample IDs only in DB (first 50):')
        print(only_in_db[:50])

    # Optional: show one example full row from DB for an ID present only in DB
    if only_in_db:
        ex = only_in_db[0]
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute('SELECT * FROM gebaeudebrueter WHERE id=?', (ex,))
        row = cur.fetchone()
        conn.close()
        print(f"\nExample row only in DB (id={ex}):")
        print(row)


if __name__ == '__main__':
    main()
