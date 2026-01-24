import sqlite3, csv, os
DB='brueter.sqlite'
OUT='reports/unknown_examples.csv'
os.makedirs('reports', exist_ok=True)
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()
# Determine species flag columns present
cur.execute("PRAGMA table_info(gebaeudebrueter)")
cols=[r[1] for r in cur.fetchall()]
species_cols=[c for c in ['sperling','mauersegler','schwalbe','star','fledermaus','andere'] if c in cols]
# Build WHERE clause: sum of COALESCE(species,0)=0
if species_cols:
    expr = ' + '.join([f"COALESCE({c},0)" for c in species_cols])
    where = f"({expr})=0"
else:
    # no known species columns -> nothing to export
    print('No species flag columns found; exiting')
    raise SystemExit(0)
# Columns to export
export_cols = ['rowid','web_id','bezirk','plz','ort','strasse','beschreibung','besonderes','update_date']
# Filter to existing columns
cur.execute('PRAGMA table_info(gebaeudebrueter)')
allcols=[r[1] for r in cur.fetchall()]
export_cols = [c for c in export_cols if (c in allcols) or c=='rowid']
# Query
q = f"SELECT rowid, {', '.join([c for c in export_cols if c!='rowid'])} FROM gebaeudebrueter WHERE {where} ORDER BY rowid DESC"
cur.execute(q)
rows = cur.fetchall()
if not rows:
    print('No unknown-example rows found')
else:
    # use cursor.description to get the actual returned column names/order
    colnames = [d[0] for d in cur.description]
    with open(OUT,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(colnames)
        for r in rows:
            w.writerow(list(r))
    print('Wrote', len(rows), 'rows to', OUT)
conn.close()
