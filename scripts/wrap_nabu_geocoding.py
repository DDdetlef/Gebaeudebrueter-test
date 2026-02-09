import os
import sys
import argparse
import subprocess
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'


def run_subprocess(script: Path, env: dict, args: list = None):
    cmd = [sys.executable, str(script)] + (args or [])
    res = subprocess.run(cmd, env=env, cwd=str(ROOT))
    if res.returncode != 0:
        print(f"ERROR running {script.name} (exit {res.returncode})")
        raise SystemExit(res.returncode)


def db_counts(db_path: Path):
    try:
        c = sqlite3.connect(str(db_path))
        cur = c.cursor()
        cur.execute('select count(*) from gebaeudebrueter where new=1')
        new_cnt = cur.fetchone()[0]
        cur.execute('select count(*) from geolocation_osm')
        osm_cnt = cur.fetchone()[0]
        cur.execute('select count(*) from geolocation_google')
        google_cnt = cur.fetchone()[0]
        c.close()
        return new_cnt, osm_cnt, google_cnt
    except Exception as e:
        print('DB count error:', e)
        return None, None, None


def main():
    ap = argparse.ArgumentParser(description='Wrapper: run nabuPageScraper then geocode new entries')
    ap.add_argument('--db', default=str(ROOT / 'brueter.sqlite'), help='Path to SQLite DB')
    ap.add_argument('--ua-base', default=os.environ.get('NOMINATIM_USER_AGENT', 'Gebaeudebrueter/2026-02'), help='Nominatim user agent base')
    ap.add_argument('--ua-url', default=os.environ.get('NOMINATIM_URL'), help='Project URL for UA')
    ap.add_argument('--ua-email', default=os.environ.get('NOMINATIM_EMAIL'), help='Contact email for UA')
    ap.add_argument('--google-key', default=os.environ.get('GOOGLE_API_KEY'), help='Google Geocoding API key')
    ap.add_argument('--limit', type=int, default=None, help='Limit number of entries to geocode')
    args = ap.parse_args()

    env = os.environ.copy()
    # propagate identity
    env['NOMINATIM_USER_AGENT'] = args.ua_base
    if args.ua_url:
        env['NOMINATIM_URL'] = args.ua_url
    if args.ua_email:
        env['NOMINATIM_EMAIL'] = args.ua_email
    if args.google_key:
        env['GOOGLE_API_KEY'] = args.google_key

    db_path = Path(args.db)

    print('Step 0: DB counts (before)')
    new_cnt, osm_cnt, google_cnt = db_counts(db_path)
    print(f'before: new={new_cnt}, geolocation_osm={osm_cnt}, geolocation_google={google_cnt}')

    print('Step 1: Run nabuPageScraper to fetch/update entries')
    # nabuPageScraper.py uses hardcoded DB path 'brueter.sqlite'; run from repo root
    run_subprocess(SCRIPTS / 'nabuPageScraper.py', env)

    print('Step 2: Geocode new entries (OSM-first, Google optional)')
    geo_args = []
    if args.limit is not None:
        geo_args.append(f'--limit={args.limit}')
    run_subprocess(SCRIPTS / 'generateLocationForPageMap.py', env, args=geo_args)

    print('Step 3: DB counts (after)')
    new_cnt, osm_cnt, google_cnt = db_counts(db_path)
    print(f'after: new={new_cnt}, geolocation_osm={osm_cnt}, geolocation_google={google_cnt}')

    print('Done: wrapper completed successfully.')


if __name__ == '__main__':
    main()
