import csv
om_path='reports/omitted_from_maps_ci.csv'
bad_path='reports/bad_coords.csv'
# collect web ids from omitted file (gb__web_id)
om_ids=set()
with open(om_path, newline='', encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
        try:
            om_ids.add(int(row.get('gb__web_id') or row.get('gb__id') or 0))
        except:
            pass
bad_ids=set()
with open(bad_path, newline='', encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
        try:
            bad_ids.add(int(row.get('web_id') or row.get('rowid') or 0))
        except:
            pass
print('omitted_count', len(om_ids))
print('bad_coords_count', len(bad_ids))
print('overlap', len(om_ids & bad_ids))
print('unique_omitted_not_bad', len(om_ids - bad_ids))
print('unique_bad_not_omitted', len(bad_ids - om_ids))
