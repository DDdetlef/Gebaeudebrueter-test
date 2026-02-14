import os
import shutil
import sqlite3

DB = 'brueter.sqlite'
BACKUP = 'brueter.sqlite.bak'
PRE_RESTORE = 'brueter.sqlite.pre_restore.bak'


def count_rows(db_path):
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM gebaeudebrueter")
        c = cur.fetchone()[0]
        conn.close()
        return c
    except Exception as e:
        print(f"Error reading {db_path}: {e}")
        return None


def main():
    print(f"Live DB: {DB}")
    print(f"Backup : {BACKUP}")
    live_count = count_rows(DB)
    backup_count = count_rows(BACKUP)
    print(f"Live count   = {live_count}")
    print(f"Backup count = {backup_count}")

    if backup_count is None:
        print("No usable backup found. Nothing to restore.")
        return
    if live_count is None:
        print("Live DB missing or unreadable. Restoring backup to live DB.")
    if backup_count > (live_count or 0):
        print("Backup has more entries than live DB — restoring.")
        # create pre-restore backup of current DB
        if os.path.exists(DB):
            if not os.path.exists(PRE_RESTORE):
                shutil.copyfile(DB, PRE_RESTORE)
                print(f"Created pre-restore backup: {PRE_RESTORE}")
            else:
                print(f"Pre-restore backup already exists: {PRE_RESTORE}")
        # restore
        shutil.copyfile(BACKUP, DB)
        print(f"Restored {BACKUP} -> {DB}")
        new_count = count_rows(DB)
        print(f"New live count = {new_count}")
    else:
        print("No restore needed: backup does not contain more entries.")


if __name__ == '__main__':
    main()
