import sqlite3

DB = 'brueter.sqlite'

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    for t in tables:
        cur.execute(f"SELECT count(*) FROM '{t}'")
        print(f"{t}: {cur.fetchone()[0]}")
    conn.close()

if __name__ == '__main__':
    main()
