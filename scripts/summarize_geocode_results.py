import csv
from collections import Counter

P='reports/geocode_missing_results.csv'
rows=[]
with open(P, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

prov=Counter(r.get('provider') for r in rows)
stat=Counter(r.get('status') for r in rows)

print('results_rows=', len(rows))
print('providers=', dict(prov))
print('status=', dict(stat))
