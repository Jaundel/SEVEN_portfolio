"""Execute both classifiers on the same Dolly prompts; never call a model/API."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/results/router-2026-11-14'


def classify(checkout, dataset):
    code = """import sys,json
sys.path.insert(0,sys.argv[1]+'/SEVEN')
import heuristics as h
rows=[json.loads(s) for s in open(sys.argv[2],encoding='utf-8')]
prompts=[r['instruction'].strip()+ ('\\n\\n'+r['context'].strip() if r.get('context','').strip() else '') for r in rows]
print(json.dumps([h.classify_query_type(p) for p in prompts]))
"""
    return json.loads(subprocess.check_output([sys.executable, '-c', code, str(checkout), str(dataset)], text=True, encoding='utf-8'))


def main():
    original, restored = map(Path, sys.argv[1:3])
    dataset = ROOT / 'evidence/datasets/dolly-15k.jsonl'
    rows = [json.loads(s) for s in dataset.read_text(encoding='utf-8').splitlines()]
    before, after = classify(original, dataset), classify(restored, dataset)
    assert len(rows) == len(before) == len(after) == 15011
    old = json.loads((ROOT / 'evidence/results/route_audit_summary.json').read_text())
    counts = lambda decisions: dict(Counter(r['route'] for r in decisions))
    assert counts(before) == old['routes'], 'Original audit did not reproduce'
    OUT.mkdir(parents=True, exist_ok=True)
    versions = []
    for label, path, decisions in [('Original', original, before), ('Restored', restored, after)]:
        source = path / 'SEVEN/heuristics.py'
        target = OUT / (label.lower() + '-heuristics.py')
        target.write_bytes(source.read_bytes())
        versions.append({'label':label, 'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                         'routes':counts(decisions), 'source':str(target.relative_to(ROOT)).replace('\\','/')})
    records = [{'row':i,'category':r['category'],'original':b['route'],'restored':a['route'],
                'original_reason':b['reason'],'restored_reason':a['reason']} for i,(r,b,a) in enumerate(zip(rows,before,after))]
    with (OUT/'decisions.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=records[0]);writer.writeheader();writer.writerows(records)
    summary = {'dataset':'databricks/databricks-dolly-15k', 'n':len(rows),
        'dataset_sha256':hashlib.sha256(dataset.read_bytes()).hexdigest(),
        'method':'Each unmodified classifier function executed on instruction plus optional context. Decisions only; no inference, answer grading or ground-truth route labels.',
        'versions':versions, 'changed':sum(b['route']!=a['route'] for b,a in zip(before,after)),
        'transitions':dict(Counter(b['route']+' -> '+a['route'] for b,a in zip(before,after)))}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    (ROOT/'data/route-comparison.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    prompts = ['Explain whether a triangle has three sides.', 'What is the weather in Toronto right now?',
        'Explain quantum entanglement in two sentences.', 'What is the price of a book?',
        'What is the capital of France?', 'What is the latest version of Python?']
    trace_dataset=OUT/'trace-inputs.jsonl'
    trace_dataset.write_text('\n'.join(json.dumps({'instruction':p}) for p in prompts),encoding='utf-8')
    trace_before, trace_after=classify(original,trace_dataset),classify(restored,trace_dataset)
    traces=[{'prompt':p,'original':b,'restored':a} for p,b,a in zip(prompts,trace_before,trace_after)]
    (ROOT/'data/paired-routes.json').write_text(json.dumps(traces,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
