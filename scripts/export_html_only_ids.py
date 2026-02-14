import re
import sqlite3
from pathlib import Path

HTML = Path('docs') / 'GebaeudebrueterMultiMarkers.html'
DB = 'brueter.sqlite'
OUT = Path('scripts') / 'html_only_ids.txt'


def ids_in_html(path: Path):
    text = path.read_text(encoding='utf-8')
    ids = set(map(int, re.findall(r"[?&]ID=(\d+)", text)))
    if not ids:
        ids = set(map(int, re.findall(r">(\d{2,5})<", text)))
    return ids


def ids_in_db(db_path: str):
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

    only_in_html = sorted(html_ids - db_ids)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        for idv in only_in_html:
            f.write(str(idv) + '\n')

    print(f"Wrote {len(only_in_html)} IDs to {OUT}")


if __name__ == '__main__':
    main()
