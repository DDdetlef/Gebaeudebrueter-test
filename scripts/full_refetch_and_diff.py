import os
import shutil
import sqlite3
import hashlib
import unicodedata
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from datetime import datetime
import csv

DB = 'brueter.sqlite'
BACKUP_DIR = 'backups'
REPORT_DIR = 'reports'
URL = 'http://www.gebaeudebrueter-in-berlin.de/index.php'

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# backup DB
timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
backup_path = os.path.join(BACKUP_DIR, f'brueter.sqlite.full_refetch_{timestamp}.bak')
shutil.copy2(DB, backup_path)
print('Backup created:', backup_path)

# helper functions (adapted from nabuPageScraper.py)
def sanitize_date(date_text):
    unkown = 'unbekannt'
    if not date_text:
        return unkown
    special = ['unbekannt','?','o.D.','Salinger','o.D. ','Nicht angegeben']
    if date_text in special:
        return unkown
    # some manual fixes
    fixes = {
        'Mai 2019':'01.05.2019','Juni 2014, Mai 2016':'01.06.2014','Juni 2019':'01.06.2019',
        'Mai 2018':'01.05.2018','Mai 2016':'01.05.2016','Sommer 2019':'21.06.2019','Herbst 2019':'23.09.2019',
        '18.06-15':'18.06.2015','Juli 2019':'01.07.2019','004.05.2009':'04.05.2009','04.2018':'01.04.2018',
        '28.06,16':'28.06.2016','Mai 2015':'01.05.2015','Juli 2020':'01.07.2020','Juni 2020':'01.06.2020',
        'Mai 2020':'01.05.2020','30.06./02.07.18':'02.07.2018'
    }
    if date_text in fixes:
        date_text = fixes[date_text]
    try:
        from dateutil import parser
        date = parser.parse(date_text, dayfirst=True)
        return date
    except Exception:
        return unkown


def stripped(s):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != "C")


def order_id(ahref):
    ids = []
    for link in ahref:
        if 'ID' in link.get('href',''):
            m = re.search('[0-9]+', link['href'])
            if m:
                ids.append(int(m.group(0)))
    ids.sort()
    return ids


def get_data_for_id(web_id):
    detailContent = urlopen(URL + '?ID=' + str(web_id)).read()
    soup2 = BeautifulSoup(detailContent, features="html.parser")
    table = soup2.findAll('table')
    table2 = table[4]
    td = table2.findChildren('td')
    bezirk = td[1].findChildren('input')[0]['value']
    mauersegler = 1 if td[2].findChildren('input', checked=True) else 0
    kontrolle = 1 if td[3].findChildren('input', checked=True) else 0
    plz = td[5].findChildren('input')[0]['value']
    plz = stripped(plz)
    sperling = 1 if td[6].findChildren('input', checked=True) else 0
    ersatz = 1 if td[7].findChildren('input', checked=True) else 0
    ort = td[9].findChildren('input')[0]['value']
    ort = stripped(ort)
    schwalbe = 1 if td[10].findChildren('input', checked=True) else 0
    wichtig = 1 if td[11].findChildren('input', checked=True) else 0
    strasse = td[13].findChildren('input')[0]['value']
    strasse = stripped(str(strasse))
    star = 1 if td[14].findChildren('input', checked=True) else 0
    sanierung = 1 if td[15].findChildren('input', checked=True) else 0
    anhang = td[17].findChildren('input')[0]['value']
    anhang = stripped(anhang)
    fledermaus = 1 if td[18].findChildren('input', checked=True) else 0
    verloren = 1 if td[19].findChildren('input', checked=True) else 0
    erstbeobachtung = td[21].findChildren('input')[0]['value']
    erstbeobachtung = sanitize_date(erstbeobachtung)
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


# connect DB
conn = sqlite3.connect(DB)
cur = conn.cursor()

# existing web_ids
cur.execute('SELECT web_id, checksum FROM gebaeudebrueter')
existing = {row[0]: row[1] for row in cur.fetchall()}

# fetch ids from website
content = urlopen(URL + "?find=%25").read()
soup = BeautifulSoup(content, features="html.parser")
ahref = soup.findAll('a', {'href': True})
ordered_ids = order_id(ahref)

added = []
updated = []
unchanged = []
errors = []
index = 0
total = len(ordered_ids)
for web_id in ordered_ids:
    print(f'ID = {web_id}, index = {index}, total = {total}')
    try:
        values = get_data_for_id(web_id)
    except Exception as e:
        errors.append((web_id,str(e)))
        index += 1
        continue
    checksum = values[-1]
    if web_id not in existing:
        # insert
        query = ('INSERT INTO gebaeudebrueter'
                     '(web_id, bezirk, plz, ort, strasse, anhang, erstbeobachtung, beschreibung, besonderes,'
                     'update_date, mauersegler, kontrolle, sperling, ersatz, schwalbe, wichtig,'
                     'star, sanierung, fledermaus, verloren, andere, checksum)'
                     'VALUES (?,?,?,?,?,?,?,?,?,DATETIME(\'now\'),?,?,?,?,?,?,?,?,?,?,?,?)')
        cur.execute(query, values)
        conn.commit()
        added.append(web_id)
    else:
        if existing[web_id] != checksum:
            # update
            v = values[1:] + (1, values[0])
            query = ('UPDATE gebaeudebrueter SET '
                     'bezirk=?, plz=?, ort=?, strasse=?, anhang=?, erstbeobachtung=?, beschreibung=?, besonderes=?,'
                     'update_date=DATETIME(\'NOW\'), mauersegler=?, kontrolle=?, sperling=?, ersatz=?, schwalbe=?, wichtig=?, '
                     'star=?, sanierung=?, fledermaus=?, verloren=?, andere=?, checksum=?, new=? WHERE web_id=?')
            cur.execute(query, v)
            conn.commit()
            updated.append(web_id)
        else:
            unchanged.append(web_id)
    existing[web_id] = checksum
    index += 1

conn.close()

# write reports
with open(os.path.join(REPORT_DIR,'full_refetch_added.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['web_id'])
    for wid in added:
        w.writerow([wid])
with open(os.path.join(REPORT_DIR,'full_refetch_updated.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['web_id'])
    for wid in updated:
        w.writerow([wid])
with open(os.path.join(REPORT_DIR,'full_refetch_errors.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['web_id','error'])
    for wid,err in errors:
        w.writerow([wid,err])

print('Summary: total found on site=', total)
print('Added:', len(added))
print('Updated:', len(updated))
print('Unchanged:', len(unchanged))
print('Errors:', len(errors))
print('Reports written to', REPORT_DIR)
print('DB backup at', backup_path)
