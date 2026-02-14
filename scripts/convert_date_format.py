import sqlite3
import shutil
import os
import datetime
import re

DB = 'brueter.sqlite'
BACKUP = 'brueter.sqlite.bak'


def parse_date(s):
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    # try common formats
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            continue
    # fallback: match leading YYYY-MM-DD
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        y, mo, d = m.groups()
        try:
            return datetime.date(int(y), int(mo), int(d))
        except Exception:
            return None
    return None


def convert_table(conn, table, columns):
    cur = conn.cursor()
    for col in columns:
        cur.execute(f"SELECT rowid, {col} FROM '{table}'")
        rows = cur.fetchall()
        for rowid, val in rows:
            d = parse_date(val)
            if d:
                new = d.strftime("%d.%m.%Y")
                cur.execute(f"UPDATE '{table}' SET {col}=? WHERE rowid=?", (new, rowid))
    conn.commit()


def main():
    if not os.path.exists(DB):
        print(f"Database '{DB}' not found in current directory.")
        return
    # backup
    if not os.path.exists(BACKUP):
        shutil.copyfile(DB, BACKUP)
        print(f"Backup created: {BACKUP}")
    else:
        print(f"Backup already exists: {BACKUP}")

    conn = sqlite3.connect(DB)
    try:
        convert_table(conn, 'gebaeudebrueter', ['erstbeobachtung', 'update_date'])
        cur = conn.cursor()
        cur.execute("SELECT id, erstbeobachtung, update_date FROM gebaeudebrueter LIMIT 5")
        for r in cur.fetchall():
            print(r)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
