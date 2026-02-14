from bs4 import BeautifulSoup
from urllib.request import urlopen
import hashlib
import sqlite3
import unicodedata
import dateutil.parser as parser
import os

DB_PATH = 'brueter.sqlite'
URL_BASE = 'http://www.gebaeudebrueter-in-berlin.de/index.php'
MISSING_PATH = os.path.join('reports', 'missing_webids.txt')


def sanitize_date(date_text):
    unkown = 'unbekannt'
    if not date_text:
        return unkown
    if date_text in ('', 'unbekannt', '?', 'o.D.', 'Nicht angegeben'):
        return unkown

    # small fixes seen in existing scraper
    fixes = {
        'Mai 2019': '01.05.2019', 'Juni 2014, Mai 2016': '01.06.2014', 'Juni 2019': '01.06.2019',
        'Mai 2018': '01.05.2018', 'Mai 2016': '01.05.2016', 'Sommer 2019': '21.06.2019',
        'Herbst 2019': '23.09.2019', '18.06-15': '18.06.2015', 'Juli 2019': '01.07.2019',
        '004.05.2009': '04.05.2009', '04.2018': '01.04.2018', '28.06,16': '28.06.2016',
        'Mai 2015': '01.05.2015', 'Juli 2020': '01.07.2020', 'Juni 2020': '01.06.2020',
        'Mai 2020': '01.05.2020', '30.06./02.07.18': '02.07.2018'
    }
    if date_text in fixes:
        date_text = fixes[date_text]

    try:
        d = parser.parse(date_text, dayfirst=True)
    except Exception:
        print('Cannot convert: ' + str(date_text))
        return unkown
    return d


def stripped(s):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')


def fetch_detail(web_id):
    detailContent = urlopen(URL_BASE + '?ID=' + str(web_id)).read()
    soup2 = BeautifulSoup(detailContent, features='html.parser')
    table = soup2.findAll('table')
    table2 = table[4]
    td = table2.findChildren('td')
    bezirk = td[1].findChildren('input')[0]['value']
    mauersegler = 1 if td[2].findChildren('input', checked=True) else 0
    kontrolle = 1 if td[3].findChildren('input', checked=True) else 0
    plz = stripped(td[5].findChildren('input')[0]['value'])
    sperling = 1 if td[6].findChildren('input', checked=True) else 0
    ersatz = 1 if td[7].findChildren('input', checked=True) else 0
    ort = stripped(td[9].findChildren('input')[0]['value'])
    schwalbe = 1 if td[10].findChildren('input', checked=True) else 0
    wichtig = 1 if td[11].findChildren('input', checked=True) else 0
    strasse = stripped(str(td[13].findChildren('input')[0]['value']))
    star = 1 if td[14].findChildren('input', checked=True) else 0
    sanierung = 1 if td[15].findChildren('input', checked=True) else 0
    anhang = stripped(td[17].findChildren('input')[0]['value'])
    fledermaus = 1 if td[18].findChildren('input', checked=True) else 0
    verloren = 1 if td[19].findChildren('input', checked=True) else 0
    erstbeobachtung = sanitize_date(td[21].findChildren('input')[0]['value'])
    andere = 1 if td[22].findChildren('input', checked=True) else 0
    table2 = table[5]
    td = table2.findChildren('td')
    beschreibung = td[1].findChildren('textarea')[0].text
    besonderes = td[3].findChildren('textarea')[0].text

    data = (web_id, bezirk, plz, ort, strasse, anhang, erstbeobachtung, beschreibung, besonderes, mauersegler,
            kontrolle, sperling, ersatz, schwalbe, wichtig, star, sanierung, fledermaus, verloren, andere)
    payload = ''.join(map(str, data))
    checksum = hashlib.sha3_224(payload.encode('utf-8')).hexdigest()
    return data + (checksum,)


def main():
    if not os.path.exists(MISSING_PATH):
        print(f'No {MISSING_PATH} found. Run compute_missing_webids.py first.')
        return

    with open(MISSING_PATH, 'r', encoding='utf-8') as fh:
        ids = [int(line.strip()) for line in fh if line.strip()]

    if not ids:
        print('No missing ids to process.')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for web_id in ids:
        try:
            print('Processing', web_id)
            values = fetch_detail(web_id)
            checksum = values[-1]
            cur.execute('SELECT checksum from gebaeudebrueter where web_id=?', (web_id,))
            data = cur.fetchall()
            if len(data) == 0:
                value = values
                query = ('INSERT INTO gebaeudebrueter'
                         '(web_id, bezirk, plz, ort, strasse, anhang, erstbeobachtung, beschreibung, besonderes,'
                         'update_date, mauersegler, kontrolle, sperling, ersatz, schwalbe, wichtig,'
                         'star, sanierung, fledermaus, verloren, andere, checksum)'
                         'VALUES (?,?,?,?,?,?,?,?,?,DATETIME(\'now\'),?,?,?,?,?,?,?,?,?,?,?,?)')
                cur.execute(query, value)
                conn.commit()
                print('added')
            else:
                cur.execute('SELECT checksum from gebaeudebrueter where web_id=? and checksum=?', (web_id, checksum))
                data2 = cur.fetchall()
                if len(data2) == 0:
                    value = values[1:] + (1, values[0])
                    query = ('UPDATE gebaeudebrueter SET '
                             'bezirk=?, plz=?, ort=?, strasse=?, anhang=?, erstbeobachtung=?, beschreibung=?, besonderes=?,'
                             'update_date=DATETIME(\'NOW\'), mauersegler=?, kontrolle=?, sperling=?, ersatz=?, schwalbe=?, wichtig=?,'
                             'star=?, sanierung=?, fledermaus=?, verloren=?, andere=?, checksum=?, new=? WHERE web_id=?')
                    cur.execute(query, value)
                    conn.commit()
                    print('updated')
        except Exception as e:
            print('Error processing', web_id, e)

    conn.close()


if __name__ == '__main__':
    main()
