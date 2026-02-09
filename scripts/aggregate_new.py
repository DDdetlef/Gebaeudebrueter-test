import sqlite3, csv, os

# Adjust this cutoff if you know the previous max rowid
# If not set, we'll try to detect by a marker: rows with id >= last_known_id
# For now, we infer new rows by a 'new' flag if present, otherwise by recent rowid range.

DB='brueter.sqlite'
OUT_DIR='reports'
os.makedirs(OUT_DIR, exist_ok=True)
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()
# Inspect schema
cur.execute("PRAGMA table_info(gebaeudebrueter)")
cols=[r[1] for r in cur.fetchall()]
# Prefer a 'new' column if present
if 'new' in cols:
    cur.execute("select rowid,* from gebaeudebrueter where new=1")
    rows=cur.fetchall()
else:
    # fallback: assume newly added are the ones with the latest rowids (heuristic)
    cur.execute('select max(rowid) from gebaeudebrueter')
    max_row=cur.fetchone()[0] or 0
    # take last 1000 rows as "new" (should cover the recent run)
    cutoff=max(1, max_row-1000)
    cur.execute('select rowid,* from gebaeudebrueter where rowid>?' , (cutoff,))
    rows=cur.fetchall()

if not rows:
    print('No new rows found')
    raise SystemExit(0)

# Map fields: species flags in table? common fields include sperling, mauersegler, schwalbe, star, fledermaus, andere
# We'll aggregate by checking those boolean/int columns when available, otherwise try to use 'id' or 'beschreibung'.

species_cols=[c for c in ['sperling','mauersegler','schwalbe','star','fledermaus','andere'] if c in cols]
bezirk_col = 'bezirk' if 'bezirk' in cols else None
plz_col = 'plz' if 'plz' in cols else None

# Prepare counts
from collections import Counter, defaultdict
species_counter=Counter()
by_bezirk=defaultdict(Counter)
by_plz=defaultdict(Counter)

for r in rows:
    # determine species for this row
    assigned=False
    for sc in species_cols:
        try:
            if int(r[sc])==1:
                species_counter[sc]+=1
                if bezirk_col:
                    by_bezirk[r[bezirk_col]][sc]+=1
                if plz_col:
                    by_plz[r[plz_col]][sc]+=1
                assigned=True
        except Exception:
            pass
    if not assigned:
        species_counter['unknown']+=1
        if bezirk_col:
            by_bezirk[r[bezirk_col]]['unknown']+=1
        if plz_col:
            by_plz[r[plz_col]]['unknown']+=1

# Write CSVs
with open(os.path.join(OUT_DIR,'new_by_species.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['species','count'])
    for k,v in species_counter.most_common():
        w.writerow([k,v])

with open(os.path.join(OUT_DIR,'new_by_species_by_bezirk.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    # header: bezirk, species, count
    w.writerow(['bezirk','species','count'])
    for bz,ctr in sorted(by_bezirk.items()):
        for sp,ct in ctr.items():
            w.writerow([bz,sp,ct])

with open(os.path.join(OUT_DIR,'new_by_species_by_plz.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['plz','species','count'])
    for pz,ctr in sorted(by_plz.items()):
        for sp,ct in ctr.items():
            w.writerow([pz,sp,ct])

print('Wrote CSVs to',OUT_DIR)
