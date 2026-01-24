import sqlite3, csv, os

db='brueter.sqlite'
out='reports/new_meldungen.csv'
if not os.path.isdir('reports'):
    os.makedirs('reports')
con=sqlite3.connect(db)
con.row_factory=sqlite3.Row
cur=con.cursor()
cur.execute('PRAGMA table_info(gebaeudebrueter)')
cols=[r[1] for r in cur.fetchall()]
cur.execute('select rowid,* from gebaeudebrueter order by rowid desc limit 800')
rows=cur.fetchall()[::-1]
if not rows:
    print('no rows')
else:
    with open(out,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['rowid']+cols)
        for r in rows:
            w.writerow([r[0]]+list(r[1:]))
    print('wrote',len(rows),'rows to',out)
