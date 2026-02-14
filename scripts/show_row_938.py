import sqlite3, json
conn=sqlite3.connect('brueter.sqlite')
conn.row_factory=sqlite3.Row
cur=conn.cursor()
r=cur.execute("SELECT web_id,strasse_original,strasse,has_comma,has_slash,has_range,multiple_numbers,multiple_streets,flag_has_text_after_number,text_after_number,beschreibung FROM gebaeudebrueter WHERE web_id=938").fetchone()
print(json.dumps(dict(r) if r else {}, ensure_ascii=False, indent=2))
conn.close()
