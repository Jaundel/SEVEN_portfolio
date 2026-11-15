"""Copy an allowlisted, verified full-window recording into the article."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]).resolve()
manifest=json.loads((source/'manifest.json').read_text())
report_path=Path(manifest['source_report'])
report=json.loads(report_path.read_text())
assert report['passed'] and manifest['width']==1920 and manifest['height']==1140
assert manifest['bytes']>1000000, 'Reject blank-window recording'
assets=ROOT/'assets/demo';assets.mkdir(parents=True,exist_ok=True)
evidence=ROOT/'evidence/demo';evidence.mkdir(parents=True,exist_ok=True)
for name in [manifest['video']]+[c['image'] for c in manifest['checkpoints']]:
    shutil.copy2(source/name,assets/name)
for name in ['report.json','source-snapshot.zip']:
    shutil.copy2(report_path.parent/name,evidence/name)
assert zipfile.ZipFile(evidence/'source-snapshot.zip').testzip() is None
assert all('.env' not in n and not n.endswith(('.db','.sqlite')) for n in zipfile.ZipFile(evidence/'source-snapshot.zip').namelist())
manifest['source_report']='evidence/demo/report.json'
manifest['source_capture_id']=source.name
manifest['files_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [*assets.iterdir(),evidence/'report.json',evidence/'source-snapshot.zip'] if p.is_file()}
(evidence/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(manifest['files_sha256']),'width':manifest['width'],'height':manifest['height'],'source':source.name}))
