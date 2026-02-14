import re
import sqlite3
import sys
from address_utils import sanitize_street

def main():
    if len(sys.argv) < 2:
        print('Usage: compute_cleaned_street.py <web_id>')
        sys.exit(1)
    web_id = int(sys.argv[1])
    conn = sqlite3.connect('brueter.sqlite')
    cur = conn.cursor()
    cur.execute('SELECT strasse FROM gebaeudebrueter WHERE web_id=?', (web_id,))
    row = cur.fetchone()
    if not row:
        print('No row found for', web_id)
        return
    orig = row[0]
    cleaned, flags, original = sanitize_street(orig)
    print('web_id:', web_id)
    print('original strasse:', orig)
    print('cleaned strasse:', cleaned)
    print('flags:', flags)
    conn.close()

if __name__ == '__main__':
    main()
