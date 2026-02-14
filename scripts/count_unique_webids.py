import csv
from collections import Counter
import os
p = os.path.join('reports','scraped_full_export.csv')
if not os.path.exists(p):
    print('ERROR: file not found', p)
    raise SystemExit(2)

with open(p, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    web_ids = [row.get('web_id') for row in reader]

total_rows = len(web_ids)
web_ids_nonempty = [w for w in web_ids if w not in (None, '', 'None')]
unique = set(web_ids_nonempty)
dup_counts = [k for k,v in Counter(web_ids_nonempty).items() if v>1]

print('file:', p)
print('total_rows:', total_rows)
print('nonempty_web_id_rows:', len(web_ids_nonempty))
print('unique_web_id_count:', len(unique))
print('duplicate_web_ids_count:', len(dup_counts))
if len(dup_counts)>0:
    print('sample_duplicate_web_ids:', dup_counts[:10])

# check expected
expected = 2588
print('expected_web_id_count:', expected)
print('matches_expected:', len(unique) == expected)
