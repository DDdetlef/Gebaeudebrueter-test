"""
Export rows where original street != sanitized street using `address_utils.sanitize_street`.
Writes `reports/changed_streets_cleaned.csv` by default.
Usage: python scripts/export_changed_streets_cleaned.py --db=brueter.sqlite --out=reports/changed_streets_cleaned.csv
"""
import sqlite3
import os
import sys
import csv

db_path = 'brueter.sqlite'
out_path = 'reports/changed_streets_cleaned.csv'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]
    elif arg.startswith('--out='):
        out_path = arg.split('=',1)[1]

db_path = os.environ.get('BRUETER_DB', db_path)

os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

try:
    from scripts.address_utils import sanitize_street
except Exception:
    # try relative import
    try:
        from address_utils import sanitize_street
    except Exception as e:
        raise RuntimeError('Cannot import sanitize_street from scripts/address_utils.py') from e

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT web_id, strasse_original, strasse, plz, ort, beschreibung FROM gebaeudebrueter')
rows = cur.fetchall()

out_fields = ['web_id','db_strasse_original','db_strasse','original_used','cleaned','flag_has_comma','flag_has_slash','flag_has_range','flag_multiple_numbers','flag_multiple_streets','flag_kept_text_after_number','plz','ort','beschreibung']

written = 0
with open(out_path, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.writer(fh)
    writer.writerow(out_fields)
    for r in rows:
        db_orig = (r['strasse_original'] or '').strip()
        db_str = (r['strasse'] or '').strip()
        original_used = db_orig if db_orig else db_str
        cleaned, flags, original_returned = sanitize_street(original_used or '')
        cleaned = (cleaned or '').strip()
        # compare normalized
        if (original_used or '').strip() != cleaned:
            writer.writerow([
                r['web_id'],
                db_orig,
                db_str,
                original_used,
                cleaned,
                int(flags.get('has_comma',0)),
                int(flags.get('has_slash',0)),
                int(flags.get('has_range',0)),
                int(flags.get('multiple_numbers',0)),
                int(flags.get('multiple_streets',0)),
                int(flags.get('kept_text_after_number',0)),
                r['plz'],
                r['ort'],
                r['beschreibung']
            ])
            written += 1

conn.close()
print(f'Wrote {written} rows to {out_path}')
