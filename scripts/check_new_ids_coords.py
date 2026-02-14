import sqlite3
import csv
import os

IN_FILE = os.path.join('reports', 'new_webids_vs_otherdb.txt')
OUT_CSV = os.path.join('reports', 'new_ids_coords.csv')

def load_new_ids(path):
    ids = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                ids.append(int(line))
            except:
                pass
    return ids

def valid_float(s):
    try:
        if s is None:
            return False
        if isinstance(s, (int,float)):
            return True
        if str(s).strip()=='' or str(s).lower()=='none':
            return False
        float(s)
        return True
    except:
        return False

def main():
    ids = load_new_ids(IN_FILE)
    conn = sqlite3.connect('brueter.sqlite')
    cur = conn.cursor()

    rows_out = []
    counts = {'google':0,'osm':0,'none':0,'bad_parse':0}

    for wid in ids:
        provider='none'
        lat=''; lon=''
        # check google
        cur.execute('SELECT latitude, longitude FROM geolocation_google WHERE web_id=?', (wid,))
        r = cur.fetchone()
        if r:
            latg, longg = r[0], r[1]
            if valid_float(latg) and valid_float(longg):
                provider='google'
                lat=latg; lon=longg
            else:
                provider='bad'
        if provider=='none':
            cur.execute('SELECT latitude, longitude FROM geolocation_osm WHERE web_id=?', (wid,))
            r = cur.fetchone()
            if r:
                lato, lono = r[0], r[1]
                if valid_float(lato) and valid_float(lono):
                    provider='osm'
                    lat=lato; lon=lono
                else:
                    provider='bad'

        if provider=='google':
            counts['google'] += 1
        elif provider=='osm':
            counts['osm'] += 1
        elif provider=='bad':
            counts['bad_parse'] += 1
            provider='none'
            counts['none'] += 1
        else:
            counts['none'] += 1

        rows_out.append((wid, provider, lat, lon))

    os.makedirs('reports', exist_ok=True)
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['web_id','provider','lat','lon'])
        for r in rows_out:
            w.writerow(r)

    print('checked=', len(ids))
    print('google=', counts['google'])
    print('osm=', counts['osm'])
    print('none=', counts['none'])
    print('bad_parse=', counts['bad_parse'])
    print('wrote=', OUT_CSV)

if __name__ == '__main__':
    main()
