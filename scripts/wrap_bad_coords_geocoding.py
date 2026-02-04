import os
import sys
import argparse
import subprocess
import sqlite3
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
REPORTS = ROOT / 'reports'


def run_subprocess(script: Path, env: dict):
    cmd = [sys.executable, str(script)]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(ROOT))
    if res.returncode != 0:
        print(f"ERROR running {script.name}:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        raise SystemExit(res.returncode)
    # stream useful stdout
    if res.stdout:
        print(res.stdout.strip())


def summarize_output(csv_path: Path):
    if not csv_path.exists():
        print(f"Output file not found: {csv_path}")
        return
    with csv_path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        rows = list(r)
    ok = sum(1 for row in rows if (row.get('status') or '') == 'OK')
    osm = sum(1 for row in rows if (row.get('provider') or '') == 'osm' and (row.get('status') or '') == 'OK')
    google = sum(1 for row in rows if (row.get('provider') or '') == 'google' and (row.get('status') or '') == 'OK')
    print(f"Output summary: rows={len(rows)}, OK={ok}, osm={osm}, google={google}")


def db_counts(db_path: Path):
    try:
        c = sqlite3.connect(str(db_path))
        cur = c.cursor()
        cur.execute('select count(*) from geolocation_osm')
        osm = cur.fetchone()[0]
        cur.execute('select count(*) from geolocation_google')
        google = cur.fetchone()[0]
        print(f"DB counts: geolocation_osm={osm}, geolocation_google={google}")
        c.close()
    except Exception as e:
        print('DB count error:', e)


def main():
    ap = argparse.ArgumentParser(description='Wrapper: geocode bad_coords and apply to DB')
    ap.add_argument('--db', default=str(ROOT / 'brueter.sqlite'), help='Path to SQLite DB')
    ap.add_argument('--in', dest='input_csv', default=str(REPORTS / 'bad_coords.csv'), help='Input CSV (bad coords)')
    ap.add_argument('--out', dest='output_csv', default=str(REPORTS / 'geocode_bad_coords_results.csv'), help='Output CSV for geocoded results')
    ap.add_argument('--ua-base', default=os.environ.get('NOMINATIM_USER_AGENT', 'Gebaeudebrueter/2026-02'), help='Nominatim user agent base')
    ap.add_argument('--ua-url', default=os.environ.get('NOMINATIM_URL'), help='Project URL for UA')
    ap.add_argument('--ua-email', default=os.environ.get('NOMINATIM_EMAIL'), help='Contact email for UA')
    ap.add_argument('--google-key', default=os.environ.get('GOOGLE_API_KEY'), help='Google Geocoding API key')
    args = ap.parse_args()

    env = os.environ.copy()
    env['BRUETER_DB'] = args.db
    env['BAD_COORDS_CSV'] = str(Path(args.input_csv).resolve())
    env['BAD_COORDS_OUT'] = str(Path(args.output_csv).resolve())
    env['NOMINATIM_USER_AGENT'] = args.ua_base
    if args.ua_url:
        env['NOMINATIM_URL'] = args.ua_url
    if args.ua_email:
        env['NOMINATIM_EMAIL'] = args.ua_email
    if args.google_key:
        env['GOOGLE_API_KEY'] = args.google_key

    print('Step 1: Geocode bad coords')
    run_subprocess(SCRIPTS / 'geocode_bad_coords.py', env)
    summarize_output(Path(args.output_csv))

    print('Step 2: Apply results to DB')
    run_subprocess(SCRIPTS / 'apply_bad_coords_results.py', env)
    db_counts(Path(args.db))

    print('Done: wrapper completed successfully.')


if __name__ == '__main__':
    main()
