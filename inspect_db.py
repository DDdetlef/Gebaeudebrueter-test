import sqlite3
import json

DB='brueter.sqlite'

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    output = {}
    for t in tables:
        cur.execute(f"SELECT count(*) FROM '{t}'")
        count = cur.fetchone()[0]
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = [c[1] for c in cur.fetchall()]
        cur.execute(f"SELECT * FROM '{t}' LIMIT 5")
        rows = cur.fetchall()
        output[t] = { 'count': count, 'columns': cols, 'sample_rows': rows }
    print(json.dumps(output, default=str, indent=2, ensure_ascii=False))

if __name__=='__main__':
    main()
