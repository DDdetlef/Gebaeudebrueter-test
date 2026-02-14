import re
import csv
from pathlib import Path

HTML = Path('docs') / 'GebaeudebrueterMultiMarkers.html'
IDS_FILE = Path('scripts') / 'html_only_ids.txt'
OUT_CSV = Path('scripts') / 'html_only_records.csv'


def parse_html_blocks(text):
    # find all var html_<hash> = $(`...`);
    pattern = re.compile(r"var\s+(html_[0-9a-f]+)\s*=\s*\$\(`([\s\S]*?)`\)", re.MULTILINE)
    blocks = {}
    for m in pattern.finditer(text):
        var = m.group(1)
        content = m.group(2)
        blocks[var] = content
    return blocks


def ids_in_block(content):
    # find all IDs referenced as ?ID=123 or index.php?ID=123 or >123< (the DB link)
    ids = set(map(int, re.findall(r"[?&]ID=(\d+)", content)))
    if not ids:
        ids = set(map(int, re.findall(r">(\d{2,5})<", content)))
    return ids


def main():
    if not HTML.exists():
        print(f"HTML file not found: {HTML}")
        return
    if not IDS_FILE.exists():
        print(f"IDs file not found: {IDS_FILE}")
        return

    text = HTML.read_text(encoding='utf-8')
    blocks = parse_html_blocks(text)

    # build id -> content mapping
    id_map = {}
    for var, content in blocks.items():
        for idv in ids_in_block(content):
            id_map.setdefault(idv, []).append((var, content))

    ids_to_export = [int(line.strip()) for line in IDS_FILE.read_text(encoding='utf-8').splitlines() if line.strip()]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'html_var', 'popup_html'])
        for idv in ids_to_export:
            rows = id_map.get(idv)
            if not rows:
                writer.writerow([idv, '', ''])
            else:
                # if multiple entries, write multiple rows
                for var, content in rows:
                    # collapse whitespace and preserve HTML
                    writer.writerow([idv, var, content.replace('\n', ' ').strip()])

    print(f"Wrote records for {len(ids_to_export)} IDs to {OUT_CSV}")


if __name__ == '__main__':
    main()
