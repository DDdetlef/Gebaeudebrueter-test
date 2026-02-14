import sqlite3

def main():
    db = 'brueter.sqlite'
    ids = [2230,2233,2240,2241,2254,2256,2264,2266,2267]
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    q = ('SELECT web_id,strasse,strasse_original,has_comma,has_slash,has_range,'
         'multiple_numbers,multiple_streets,kept_text_after_number,beschreibung '
         'FROM gebaeudebrueter WHERE web_id IN (%s)') % (','.join('?'*len(ids)))
    cur.execute(q, ids)
    rows = cur.fetchall()
    if not rows:
        print('No rows found for test ids.')
    for r in rows:
        print('---')
        print('web_id:', r[0])
        print('strasse (orig):', r[1])
        print('strasse_original:', r[2])
        print('flags: has_comma=%s has_slash=%s has_range=%s multiple_numbers=%s multiple_streets=%s kept_text_after_number=%s' % tuple(r[3:9]))
        print('beschreibung:', (r[9] or '')[:400])
    conn.close()

if __name__ == '__main__':
    main()
