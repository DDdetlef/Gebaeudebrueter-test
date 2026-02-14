#!/usr/bin/env python3
"""Orchestrate the full workflow:

- run scraper
- run data cleaning
- prepare missing coords
- filter missing by species
- create geocode batches (optionally run geocoder)
- apply geocode results (optional)
- convert date format
- regenerate maps/html

Usage: run_full_pipeline.py [--geocode] [--apply-results] [--batch-size N]
"""
from pathlib import Path
import subprocess
import sys
import importlib.util
import argparse
import os


SCRIPTS = Path('scripts')


def exists(p):
    return Path(p).exists()


def run_cmd(cmd, check=False, env=None):
    print('RUN:', ' '.join(cmd))
    r = subprocess.run(cmd, check=check, text=True, env=env, capture_output=True)
    # return (returncode, stdout, stderr)
    return (r.returncode, r.stdout or '', r.stderr or '')


def import_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--geocode', action='store_true', help='Run geocoder for batches')
    ap.add_argument('--apply-results', action='store_true', help='Apply geocode results to DB')
    ap.add_argument('--batch-size', type=int, default=50)
    args = ap.parse_args()

    steps = []

    # 1. Scrape
    summary = []
    scraper = SCRIPTS / 'nabuPageScraper.py'
    if scraper.exists():
        print('\n=== Step: run scraper ===')
        rc, out, err = run_cmd([sys.executable, str(scraper)])
        summary.append({'step': 'scrape', 'script': str(scraper), 'present': True, 'returncode': rc})
    else:
        print('Scraper not found, skipping:', scraper)
        summary.append({'step': 'scrape', 'script': str(scraper), 'present': False, 'returncode': None})

    # 2. Data cleansing
    cleanse = SCRIPTS / 'data_cleansing.py'
    if cleanse.exists():
        print('\n=== Step: data cleansing ===')
        rc, out, err = run_cmd([sys.executable, str(cleanse)])
        summary.append({'step': 'data_cleansing', 'script': str(cleanse), 'present': True, 'returncode': rc})
    else:
        print('Data cleansing script not found, skipping')
        summary.append({'step': 'data_cleansing', 'script': str(cleanse), 'present': False, 'returncode': None})

    # 3. Prepare missing coords
    prepare = SCRIPTS / 'prepare_missing_coords.py'
    if prepare.exists():
        print('\n=== Step: prepare missing coords ===')
        rc, out, err = run_cmd([sys.executable, str(prepare)])
        summary.append({'step': 'prepare_missing_coords', 'script': str(prepare), 'present': True, 'returncode': rc})
    else:
        print('prepare_missing_coords.py not found, skipping')
        summary.append({'step': 'prepare_missing_coords', 'script': str(prepare), 'present': False, 'returncode': None})

    # 4. Filter missing by species
    filter_script = SCRIPTS / 'filter_missing_by_species.py'
    if filter_script.exists():
        print('\n=== Step: filter missing by species ===')
        rc, out, err = run_cmd([sys.executable, str(filter_script)])
        summary.append({'step': 'filter_missing_by_species', 'script': str(filter_script), 'present': True, 'returncode': rc})
    else:
        print('filter_missing_by_species.py not found, skipping')
        summary.append({'step': 'filter_missing_by_species', 'script': str(filter_script), 'present': False, 'returncode': None})

    # 5. Batch geocoding (create batches and optionally run geocoder)
    print('\n=== Step: batch creation (and optional geocoding) ===')
    run_batch_mod = None
    run_batch_path = SCRIPTS / 'run_geocode_batch.py'
    if run_batch_path.exists():
        run_batch_mod = import_module(run_batch_path)
    else:
        print('run_geocode_batch.py not found; cannot create batches automatically')

    offset = 0
    batch_size = args.batch_size
    created_any = False
    batches_created = 0
    batches_geocoded = 0
    while True:
        if run_batch_mod is None:
            break
        ok = run_batch_mod.make_batch(batch_size, offset)
        if not ok:
            break
        created_any = True
        batches_created += 1
        if args.geocode:
            # run geocode_missing.py using the batch file env
            env = os.environ.copy()
            env['MISSING_CSV'] = os.path.abspath('reports/missing_coords_batch.csv')
            geocoder = SCRIPTS / 'geocode_missing.py'
            if geocoder.exists():
                rc, out, err = run_cmd([sys.executable, str(geocoder)], env=env)
                if rc == 0:
                    batches_geocoded += 1
            else:
                print('geocode_missing.py not found; skipping geocoding')
        offset += batch_size

    summary.append({'step': 'batch_creation', 'script': str(run_batch_path), 'present': run_batch_path.exists(), 'batches_created': batches_created, 'batches_geocoded': batches_geocoded})
    if not created_any:
        print('No batches created (no missing rows?)')

    # 6. Apply geocode results
    if args.apply_results:
        apply_script = SCRIPTS / 'apply_geocode_results.py'
        if apply_script.exists():
            print('\n=== Step: apply geocode results ===')
            rc, out, err = run_cmd([sys.executable, str(apply_script)])
            summary.append({'step': 'apply_geocode_results', 'script': str(apply_script), 'present': True, 'returncode': rc})
        else:
            print('apply_geocode_results.py not found; skipping apply')
            summary.append({'step': 'apply_geocode_results', 'script': str(apply_script), 'present': False, 'returncode': None})

    # 7. Convert date format
    convert = SCRIPTS / 'convert_date_format.py'
    if convert.exists():
        print('\n=== Step: convert date format ===')
        rc, out, err = run_cmd([sys.executable, str(convert)])
        summary.append({'step': 'convert_date_format', 'script': str(convert), 'present': True, 'returncode': rc})
    else:
        print('convert_date_format.py not found; skipping')
        summary.append({'step': 'convert_date_format', 'script': str(convert), 'present': False, 'returncode': None})

    # 8. Regenerate maps / html
    maps = [SCRIPTS / 'generateLocationMap.py', SCRIPTS / 'generateMultiSpeciesMap.py']
    maps_run = []
    for m in maps:
        if m.exists():
            print(f'\n=== Step: run {m.name} ===')
            rc, out, err = run_cmd([sys.executable, str(m)])
            maps_run.append({'script': str(m), 'returncode': rc})
        else:
            print('Map generation script not found, skipping:', m.name)
            maps_run.append({'script': str(m), 'returncode': None})
    summary.append({'step': 'map_generation', 'maps': maps_run})

    # write summary report
    repdir = Path('reports')
    repdir.mkdir(exist_ok=True)
    summary_file = repdir / 'pipeline_summary.txt'
    with summary_file.open('w', encoding='utf-8') as sf:
        sf.write('Pipeline run summary\n')
        sf.write('====================\n')
        for s in summary:
            sf.write(str(s) + '\n')
        sf.write('\nBatches created: %s\n' % (batches_created,))
        sf.write('Batches geocoded: %s\n' % (batches_geocoded,))
    print('\nWrote summary to', summary_file)

    print('\nPipeline finished.')


if __name__ == '__main__':
    main()
