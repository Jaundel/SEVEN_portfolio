"""Package captured code plus explicitly allowlisted setup metadata; never env/history."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('application', type=Path)
args = parser.parse_args()
app = args.application.resolve()
destination = ROOT / 'evidence/demo'
captured = destination / 'source-snapshot.zip'
support = ['SETUP.md', 'RESTORATION.md', 'README.md', 'SEVEN/requirements.txt',
           'requirements-demo.txt', 'apps/elia/pyproject.toml',
           'apps/elia/README.md', 'apps/elia/LICENSE']
report = json.loads((destination / 'report.json').read_text(encoding='utf-8'))
files = {}
with zipfile.ZipFile(captured) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        files[name] = archive.read(name)
for name, digest in report['source_sha256'].items():
    name = name.replace('\\', '/')
    assert hashlib.sha256(files[name]).hexdigest() == digest, name
for name in support:
    assert name not in files
    files[name] = (app / name).read_bytes()
packages = json.loads(subprocess.check_output([
    str(app / '.venv/Scripts/python.exe'), '-m', 'pip', 'list', '--format=json'], text=True))
files['requirements-resolved.txt'] = ('# Installed application environment at packaging time; Python 3.12, Windows.\n'
    '# Install Elia separately with --no-deps -e apps/elia, as described in SETUP.md.\n' +
    ''.join(f"{p['name']}=={p['version']}\n" for p in sorted(packages, key=lambda p: p['name'].lower())
            if p['name'].lower() not in {'elia-chat', 'elia_chat', 'pip'})).encode()
files['CAPTURE-SOURCE.md'] = (
    '# Recorded SEVEN application\n\n'
    'The Python, PowerShell and SCSS files come byte-for-byte from source-snapshot.zip, '
    'captured with the November 14, 2026 full-window walkthrough. '
    'Setup documents, package metadata, dependency lists and the Elia MIT licence '
    'were added from the restored checkout during packaging. They are not measured results.\n\n'
    'Start with SETUP.md. No environment files, credentials, chat databases, runtime '
    'binaries or model weights are included. The Ryzen AI launcher expects the runtime '
    'already installed; another compatible backend can use the documented Python entry point.\n\n'
    'The terminal interface adapts Darren Burns\' Elia; retain apps/elia/LICENSE. '
    'Original team roles are in README.md. Do not infer that SEVEN authored Elia.\n').encode()
assert all(not any(part.startswith('.') for part in Path(n).parts) and
           not n.lower().endswith(('.db', '.sqlite', '.sqlite3', '.onnx')) for n in files)
target = destination / 'restored-source.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, contents in sorted(files.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 11, 15, 3, 23, 12))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, contents)
manifest = {'captured_source_sha256': hashlib.sha256(captured.read_bytes()).hexdigest(),
    'archive_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
    'supplemental_files': support + ['requirements-resolved.txt', 'CAPTURE-SOURCE.md'],
    'files_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in sorted(files.items())}}
(destination / 'source-package.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'archive': str(target.relative_to(ROOT)), 'files': len(files)}))
