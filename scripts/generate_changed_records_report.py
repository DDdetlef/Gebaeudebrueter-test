"""
Generate CSV report for records where street was changed (the 1107 entries).
It detects rows where `beschreibung` starts with the note "(Originaleintrag_Straße) ..."
or where `strasse_original` differs from current `strasse`.

Output: `reports/changed_records_report.csv`
"""
import sqlite3
import os
import sys
import csv

db_path = 'brueter.sqlite'
out_path = 'reports/changed_records_report.csv'
for arg in sys.argv[1:]:
    if arg.startswith('--db='):
        db_path = arg.split('=',1)[1]
    elif arg.startswith('--out='):
        out_path = arg.split('=',1)[1]

db_path = os.environ.get('BRUETER_DB', db_path)
os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = "SELECT web_id, strasse_original, strasse, plz, ort, beschreibung, has_comma, has_slash, has_range, multiple_numbers, multiple_streets, flag_has_text_after_number, text_after_number FROM gebaeudebrueter"
rows = cur.execute(query).fetchall()

out_fields = ['web_id','original_used','current_strasse','plz','ort','has_comma','has_slash','has_range','multiple_numbers','multiple_streets','flag_has_text_after_number','text_after_number','beschreibung']

written = 0
with open(out_path, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.writer(fh)
    writer.writerow(out_fields)
    for r in rows:
        web_id = r['web_id']
        beschr = r['beschreibung'] or ''
        orig_used = ''
        if beschr.startswith('(Originaleintrag_Straße) '):
            # extract the original_used from first line
            first_line = beschr.splitlines()[0]
            orig_used = first_line.replace('(Originaleintrag_Straße) ', '', 1).strip()
        elif r['strasse_original'] and str(r['strasse_original']).strip():
            orig_used = str(r['strasse_original']).strip()
        else:
            # no recorded original; skip
            continue

        current = r['strasse'] or ''
        # only include rows where original differs from current
        if orig_used.strip() == (current or '').strip():
            continue

        writer.writerow([
            web_id,
            orig_used,
            current,
            r['plz'],
            r['ort'],
            r['has_comma'] or 0,
            r['has_slash'] or 0,
            r['has_range'] or 0,
            r['multiple_numbers'] or 0,
            r['multiple_streets'] or 0,
            (r['flag_has_text_after_number'] if 'flag_has_text_after_number' in r.keys() else 0) or 0,
            (r['text_after_number'] if 'text_after_number' in r.keys() else '') or '',
            beschr.replace('\r\n','\n')
        ])
        written += 1

conn.close()
print(f'Wrote {written} rows to {out_path}')
