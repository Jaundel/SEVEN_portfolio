"""Static checks for the article assets and estimator values.
Run python tools/check_article.py [path/to/SEVEN/energy.py]
The optional source file must match the tracked source SHA-256.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import csv, hashlib, importlib.util, json, math, sys
ROOT=Path(__file__).resolve().parents[1]
class Document(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.refs=[]; self.images=[]; self.iframes=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        for k in ['src','href']:
            if k in a: self.refs.append(a[k])
        if tag=='img': self.images.append(a)
        if tag=='iframe': self.iframes+=1
h=Document(); h.feed((ROOT/'index.html').read_text())
assert len(h.ids)==len(set(h.ids)), 'Duplicate IDs'
assert h.iframes==0, 'Interactive demo iframe remains'
for img in h.images: assert img.get('alt'), 'Missing alt text'
for ref in h.refs:
    p=urlsplit(ref)
    if p.scheme or p.netloc or p.path.startswith('/'): continue
    if p.path: assert (ROOT/unquote(p.path)).is_file(), f'Missing local asset: {ref}'
    elif p.fragment: assert p.fragment in h.ids, f'Missing anchor: {ref}'
profiles=json.loads((ROOT/'data/energy_profiles.json').read_text())
rows=list(csv.DictReader((ROOT/'data/energy_estimates.csv').open()))
for row in rows:
    for key in ['local','cloud']:
        expected=int(row['tokens'])*profiles[key]['joules_per_token']/3600
        assert math.isclose(float(row[key+'_estimate_Wh']),expected,abs_tol=5.1e-10)
print('PASS: local assets, anchors, alt text, no iframe, CSV formulas')
if len(sys.argv)>1:
    source=Path(sys.argv[1]); raw=source.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==profiles['source_sha256']
    spec=importlib.util.spec_from_file_location('seven_energy_verified',source)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    for row in rows:
        n=int(row['tokens'])
        assert math.isclose(mod.estimate_local_energy(n, mod.DEFAULT_LOCAL_PROFILE).watt_hours,float(row['local_estimate_Wh']),abs_tol=5.1e-10)
        assert math.isclose(mod.estimate_cloud_energy(n, mod.DEFAULT_CLOUD_PROFILE).watt_hours,float(row['cloud_estimate_Wh']),abs_tol=5.1e-10)
    assert mod.estimate_local_energy(None, mod.DEFAULT_LOCAL_PROFILE).tokens==500
    assert mod.estimate_cloud_energy(None, mod.DEFAULT_CLOUD_PROFILE).tokens==500
    print('PASS: actual pinned SEVEN estimators match all plotted sample values and fallback')
