"""Measure unchanged SEVEN local inference on a seeded GSM8K test sample.

python evidence/measure_local.py C:/Users/jaund/projects/SEVEN

Requires requests, Windows battery WMI, and the cached Ryzen AI backend at
127.0.0.1:8081. No cloud calls. Battery telemetry covers the entire laptop,
including this logger and other active applications. Loaded idle intervals
are references, not a controlled estimate of model-only energy.
"""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
import os
import random
import re
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / 'results' / ('2026-11-12-restored' if '--restored' in sys.argv else '2026-11-12-templated' if '--templated' in sys.argv else '2026-11-12')
DATA = HERE / 'datasets' / 'gsm8k-test.jsonl'

def stamp():
    return round(time.time() * 1000)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def number(text):
    matches = re.findall(r'-?\d[\d,]*(?:\.\d+)?', text)
    return Decimal(matches[-1].replace(',', '')) if matches else None

def main(seven):
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'gsm8k-local.jsonl'
    if target.exists():
        raise SystemExit('Refusing to overwrite a measured run. Archive it before repeating.')
    os.environ['LEMONADE_BASE_URL'] = 'http://127.0.0.1:8081/v1'
    os.environ['LEMONADE_MODEL'] = 'Llama-3.2-1B-Instruct-Hybrid'
    os.environ['LEMONADE_TIMEOUT_SECONDS'] = '120'
    sys.path.insert(0, str(seven / 'SEVEN'))
    from local_model import ask_local
    from heuristics import classify_query_type, response_shows_uncertainty
    from prompts import build_local_prompt, get_system_prompt_local
    health = requests.get('http://127.0.0.1:8081/health', timeout=5).json()
    health.pop('model_path', None)
    dataset = [json.loads(x) for x in DATA.read_text(encoding='utf-8').splitlines()]
    indices = random.Random(7).sample(range(len(dataset)), 60)
    source_files = ['local_model.py', 'heuristics.py', 'prompts.py', 'energy.py']
    meta = {
        'date': '2026-11-12', 'dataset': 'openai/gsm8k test',
        'dataset_url': 'https://github.com/openai/grade-school-math/blob/master/grade_school_math/data/test.jsonl',
        'dataset_sha256': sha(DATA), 'seed': 7, 'rows': indices,
        'seven_commit': subprocess.check_output(['git', '-C', str(seven), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': {x: sha(seven / 'SEVEN' / x) for x in source_files},
        'working_tree_modified': bool(subprocess.check_output(['git', '-C', str(seven), 'diff', '--name-only'], text=True).strip()),
        'backend': health, 'temperature': 0.7, 'max_tokens': 512,
        'template_configuration': 'bundled Jinja template exposed in tokenizer_config.json' if '--templated' in sys.argv or '--restored' in sys.argv else 'original cached configuration; backend plaintext fallback',
        'method': 'Force every sampled question through build_local_prompt + get_system_prompt_local + ask_local, unchanged SEVEN local path; record classifier and uncertainty decisions separately. Last numeric value must equal GSM8K reference after ####. One stochastic response per question; no retries for correctness.',
        'power_scope': 'Whole-laptop battery discharge, approximately 1 Hz, trapezoidal integration. Other active applications and logger included; no model-only, wall-plug or cloud measurement.',
        'phases': [],
    }
    if '--restored' in sys.argv:
        meta['method'] = meta['method'].replace('unchanged SEVEN local path', 'restored SEVEN working-tree local path; source hashes pin the modified adapter, heuristic and prompts')
    def save_meta():
        (OUT / 'run.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    def call(q):
        with contextlib.redirect_stdout(io.StringIO()):
            return ask_local(build_local_prompt(user_query=q, allow_richer_context=False),
                system_prompt=get_system_prompt_local(), temperature=0.7, max_tokens=512)
    print('Warmup', flush=True)
    call('What is 2 + 2?')
    stop = OUT / 'power.stop'
    if stop.exists(): stop.unlink()
    logger = subprocess.Popen(['powershell.exe', '-NoProfile', '-File', str(HERE / 'power_log.ps1'),
        str(OUT / 'battery.csv'), str(stop)], creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        with target.open('w', encoding='utf-8') as stream:
            for block in range(3):
                start = stamp()
                print(f'Loaded idle baseline {block + 1}/4 (30 s)', flush=True)
                time.sleep(30)
                meta['phases'].append({'kind': 'idle', 'start_ms': start, 'end_ms': stamp()})
                block_start = stamp()
                for offset, idx in enumerate(indices[block * 20:(block + 1) * 20]):
                    row = dataset[idx]
                    start = stamp()
                    response = call(row['question'])
                    end = stamp()
                    gold = number(row['answer'].split('####')[-1])
                    usage = response.raw.get('usage') or {}
                    rec = {'row': idx, 'block': block + 1, 'question': row['question'],
                        'reference': str(gold), 'response': response.text,
                        'prediction': str(number(response.text)),
                        'correct': number(response.text) == gold,
                        'route': classify_query_type(row['question']),
                        'would_escalate': response_shows_uncertainty(response),
                        'model': response.model, 'latency_s': response.latency_s,
                        'start_ms': start, 'end_ms': end, 'usage': usage}
                    stream.write(json.dumps(rec, ensure_ascii=False) + '\n'); stream.flush()
                    print(f'{block * 20 + offset + 1}/60 row={idx} correct={rec["correct"]} {response.latency_s:.2f}s', flush=True)
                meta['phases'].append({'kind': 'inference', 'block': block + 1, 'start_ms': block_start, 'end_ms': stamp()})
                save_meta()
            start = stamp()
            print('Final loaded idle (30 s)', flush=True)
            time.sleep(30)
            meta['phases'].append({'kind': 'idle', 'start_ms': start, 'end_ms': stamp()})
            save_meta()
    finally:
        stop.touch()
        logger.wait(timeout=15)
    print('Measurement complete', flush=True)

if __name__ == '__main__':
    main(Path(sys.argv[1]))
