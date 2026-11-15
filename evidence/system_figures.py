"""Execute the archived estimator and reproduce retained comparison values."""
import hashlib
import json
import math
import sys
import types
import zipfile


def comparison_data(root):
    report_path = root/'evidence/demo/report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    archive_path = root/'evidence/demo/source-snapshot.zip'
    with zipfile.ZipFile(archive_path) as archive:
        sources = {name: archive.read(name) for name in [
            'SEVEN/energy.py', 'SEVEN/router.py', 'SEVEN/heuristics.py',
            'SEVEN/api_tools.py', 'apps/elia/elia_chat/widgets/chat.py',
            'apps/elia/elia_chat/database/database.py']}
    captured_hashes={name.replace('\\','/'):digest for name,digest in report['source_sha256'].items()}
    for name, raw in sources.items():
        assert hashlib.sha256(raw).hexdigest() == captured_hashes[name]
    module = types.ModuleType('seven_archived_energy')
    sys.modules[module.__name__] = module
    exec(compile(sources['SEVEN/energy.py'], 'archived/SEVEN/energy.py', 'exec'), module.__dict__)
    cases = []
    for record in report['results']:
        meta = record['metadata']
        if meta['route'] != 'local':
            continue
        # The saved TUI metadata has Wh, not token usage. Recover the integer
        # estimator input from the captured coefficient; do not call it a new
        # tokenizer measurement. Both stored estimates must reproduce exactly.
        coefficient = module.LOCAL_PROFILES[module.DEFAULT_LOCAL_PROFILE].per_token_j
        recovered = meta['energy_wh'] * 3600 / coefficient
        n = round(recovered)
        assert math.isclose(n, recovered, abs_tol=1e-8)
        local = module.estimate_local_energy(n, module.DEFAULT_LOCAL_PROFILE)
        cloud = module.estimate_cloud_energy(n, module.DEFAULT_CLOUD_PROFILE)
        assert math.isclose(local.watt_hours, meta['energy_wh'], abs_tol=1e-12)
        assert math.isclose(cloud.watt_hours-local.watt_hours, meta['energy_saved_wh'], abs_tol=1e-12)
        cases.append({'case':record['case'], 'prompt':record['prompt'],
            'estimator_tokens':n, 'tokens_basis':'Recovered from saved Wh and archived coefficient; integer input checked against both saved estimates.',
            'local_mwh':local.watt_hours*1000, 'cloud_proxy_mwh':cloud.watt_hours*1000,
            'difference_mwh':(cloud.watt_hours-local.watt_hours)*1000,
            'local_range_mwh':[local.watt_hours_min*1000,local.watt_hours_max*1000],
            'cloud_proxy_range_mwh':[cloud.watt_hours_min*1000,cloud.watt_hours_max*1000]})
    assert [c['estimator_tokens'] for c in cases[:2]] == [62,154]
    assert len(cases)==3 and cases[2]['case']=='local-after-cloud'
    lp=module.LOCAL_PROFILES[module.DEFAULT_LOCAL_PROFILE]
    cp=module.CLOUD_PROFILES[module.DEFAULT_CLOUD_PROFILE]
    result={'basis':'Configured estimates from the archived application; no cloud electricity was measured.',
        'local':{'label':lp.label, 'joules_per_token':lp.per_token_j, 'range':[lp.per_token_j_min,lp.per_token_j_max]},
        'cloud_proxy':{'label':cp.label, 'joules_per_token':cp.per_token_j, 'range':[cp.per_token_j_min,cp.per_token_j_max],
            'unused_wh_per_query':cp.per_query_wh, 'adapter_model':'GPT-4o-mini',
            'mismatch':'GPT-4o profile is not a calibration of GPT-4o-mini.'},
        'formula':'estimated_mWh = estimator_tokens * joules_per_token / 3.6',
        'precedence':'Per-token coefficient takes precedence over the stored per-query value.',
        'missing_usage':'The archived estimator uses 500 tokens when token usage is absent or nonpositive.',
        'cases':cases,
        'source_sha256':{name:hashlib.sha256(raw).hexdigest() for name,raw in sources.items()},
        'archive_sha256':hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        'report_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest()}
    (root/'data/energy-comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
