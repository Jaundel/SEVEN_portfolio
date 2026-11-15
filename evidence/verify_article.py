"""Check article links, derived data, native captures, archives and full MP4 decoding."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from PIL import Image, ImageStat
import imageio_ffmpeg
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Article(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
        for key in ['href', 'src', 'poster']:
            if key in attrs: self.links.append(attrs[key])

def main():
    documents = {}
    for name in ['index.html','supplement.html']:
        parsed=Article(); parsed.feed((ROOT/name).read_text(encoding='utf-8'))
        assert len(parsed.ids)==len(set(parsed.ids)), f'Duplicate IDs in {name}'
        documents[name]=parsed
    doc=documents['index.html']
    linked = set()
    for document in documents.values():
      for link in document.links:
        url = urlsplit(link)
        if url.scheme or url.netloc: continue
        if url.path:
            path = ROOT / unquote(url.path)
            assert path.is_file(), f'Missing article target: {link}'
            linked.add(path)
            if url.fragment and path.name in documents:
                assert url.fragment in documents[path.name].ids, f'Missing page anchor: {link}'
        elif url.fragment:
            assert url.fragment in document.ids, f'Missing anchor: {link}'
    css = (ROOT/'article.css').read_text(encoding='utf-8') + (ROOT/'article-tokens.css').read_text(encoding='utf-8')
    for name in re.findall(r"url\(['\"]?([^)'\"]+)", css):
        assert (ROOT/urlsplit(name).path).is_file(), f'Missing CSS resource: {name}'
    for name in ['routing-comparison.svg', 'local-results.svg', 'battery-test.svg']:
        ET.parse(ROOT/'assets/figures'/name)
    figures = read('evidence/figure-manifest.json')
    assert sha(ROOT/'evidence/figure-style.json') == figures['style_sha256']
    for name,digest in figures['font_sha256'].items():
        assert sha(ROOT/'evidence/fonts'/name) == digest
    for name,digest in figures['files_sha256'].items():
        assert sha(ROOT/name) == digest
        if name.endswith('.pdf'): assert (ROOT/name).read_bytes().startswith(b'%PDF-')
    for name,color in read('evidence/figure-style.json')['colors'].items():
        assert '--'+name+':'+color+';' in css, 'Article/figure palette diverged'

    publication=read('evidence/publication-figures.json')
    for name,digest in (publication['source_sha256']|publication['files_sha256']).items():
        assert sha(ROOT/name)==digest, f'Publication figure changed: {name}'
    assert len(publication['figures'])==10
    comparison=read('data/energy-comparison.json')
    assert comparison==publication['energy_comparison']
    first=comparison['cases'][0]
    assert first['estimator_tokens']==62
    assert abs(first['local_mwh']-14.6388888888889)<1e-9
    assert abs(first['cloud_proxy_mwh']-53.3888888888889)<1e-9
    system_trace=read('data/system-trace.json')
    assert system_trace['predicates']==[False]*4 and system_trace['decision']['route']=='LOCAL'
    assert system_trace['reply']=='The capital of France is Paris.'
    model=read('evidence/model/genai_config.json')
    assert model['model']['decoder']['num_hidden_layers']==16
    vector_checks=[]
    for f in publication['figures']:
        with pymupdf.open(ROOT/'assets/figures'/(f['name']+'.pdf')) as pdf:
            assert len(pdf)==1
            page=pdf[0]
            assert abs(page.rect.width-f['width_pt'])<.1
            assert any('Poppins' in font[3] for font in page.get_fonts()), f['name']
            fonts=[]
            for font in page.get_fonts():
                embedded=pdf.extract_font(font[0])
                assert len(embedded[3])>0, (f['name'],'Font not embedded',font[3])
                fonts.append({'name':font[3],'embedded_bytes':len(embedded[3])})
            if f['name'].startswith('answer-case'):
                clip=pymupdf.Rect(0,150,348,315) if 'mobile' in f['name'] else pymupdf.Rect(0,132,385,323)
                actual=' '.join(page.get_text(clip=clip).split())
                expected=' '.join(publication['answer_case']['complete_response'].split())
                assert actual==expected, ('Verbatim response export changed',f['name'],actual)
            if f['name'].startswith('system-architecture'):
                text=page.get_text()
                assert all(s in text for s in ['Llama 3.2 1B','GPT-4o-mini','SQLite','Coinbase','3,600'])
            if f['name'].startswith('energy-comparison'):
                text=page.get_text()
                assert all(s in text for s in ['14.6','53.4','0.85','3.10','62-token'])
            vector_checks.append({'file':'assets/figures/'+f['name']+'.pdf','sha256':sha(ROOT/'assets/figures'/(f['name']+'.pdf')),'embedded_fonts':fonts,'selectable_text':True,'text_bounds_checked':True})
            for block in page.get_text('dict')['blocks']:
              if 'lines' not in block: continue
              for line in block['lines']:
                for span in line['spans']:
                  assert span['bbox'][0]>=-1 and span['bbox'][1]>=-1 and span['bbox'][2]<=page.rect.width+1 and span['bbox'][3]<=page.rect.height+1, (f['name'],span['text'],span['bbox'])
        ET.parse(ROOT/'assets/figures'/(f['name']+'.svg'))
    assert abs(publication['power_interval']['whole_laptop_wh']-.7286752433234785)<1e-9
    main=(ROOT/'index.html').read_text(encoding='utf-8')
    assert all(name not in main for name in ['route-select','answer-select','local-results.svg','routing-comparison.svg','capture-controls','class="contents"'])
    assert main.count('data-chapter=')==3
    assert 'supplement.html#responses' in main
    (ROOT/'evidence/vector-validation.json').write_text(json.dumps({'passed':True,'renderer':'PyMuPDF '+pymupdf.__version__,'figures':vector_checks},indent=2)+'\n',encoding='utf-8')

    study = read('data/study-summary.json')
    answers = read('data/answers.json')
    assert len(answers) == 60 and len({r['row'] for r in answers}) == 60
    assert [(r['correct'],r['uncertainty_triggers'],r['wrong_unflagged']) for r in study['runs']] == [(11,8,41),(13,0,47),(22,0,38)]
    for run_index, run in enumerate(study['runs']):
        raw = [json.loads(x) for x in (ROOT/run['source']).read_text(encoding='utf-8').splitlines()]
        assert len(raw) == 60
        for paired, original in zip(answers, raw):
            assert paired['row'] == original['row'] and paired['question'] == original['question']
            assert paired['reference'] == original['reference']
            record = paired['answers'][run_index]
            assert all(record[k] == v for k,v in original.items()), 'Answer browser altered raw record'
            assert record['source'] == run['source']

    route = read('evidence/results/router-2026-11-14/summary.json')
    assert route == read('data/route-comparison.json')
    assert sha(ROOT/'evidence/datasets/dolly-15k.jsonl') == route['dataset_sha256']
    with (ROOT/'evidence/results/router-2026-11-14/decisions.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == route['n'] == 15011
    assert [int(r['row']) for r in rows] == list(range(15011))
    for version, column in zip(route['versions'], ['original','restored']):
        assert sha(ROOT/version['source']) == version['sha256']
        assert dict(Counter(r[column] for r in rows)) == version['routes']
    assert dict(Counter(r['original']+' -> '+r['restored'] for r in rows)) == route['transitions']
    assert sum(r['original'] != r['restored'] for r in rows) == route['changed'] == 2556
    assert len(read('data/paired-routes.json')) == 6

    manifest = read('evidence/demo/manifest.json')
    for name, digest in manifest['files_sha256'].items():
        assert sha(ROOT/name) == digest, f'Capture changed: {name}'
    assert (manifest['width'],manifest['height']) == (1920,1140)
    assert manifest['terminal_size'] == [156,47] and manifest['ffmpeg_exit'] == 0
    seen = set()
    for checkpoint in manifest['checkpoints']:
        file = ROOT/'assets/demo'/checkpoint['image']
        with Image.open(file) as im:
            assert im.size == (1920,1140)
            assert max(ImageStat.Stat(im.convert('RGB')).stddev) > 3, 'Blank capture'
        seen.add(sha(file))
        assert 0 < checkpoint['seconds'] < 67.534
    assert len(seen) == len(manifest['checkpoints']) == 8
    report = read('evidence/demo/report.json')
    assert report['passed'] and all(v is not False for v in report['checks'].values())
    package = read('evidence/demo/source-package.json')
    assert sha(ROOT/'evidence/demo/restored-source.zip') == package['archive_sha256']
    assert sha(ROOT/'evidence/demo/source-snapshot.zip') == package['captured_source_sha256']
    for filename in ['source-snapshot.zip','restored-source.zip']:
        with zipfile.ZipFile(ROOT/'evidence/demo'/filename) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                assert not name.startswith(('/', '\\')) and '..' not in Path(name).parts
                assert not any(p.startswith('.') for p in Path(name).parts)
                assert not name.lower().endswith(('.db','.sqlite','.sqlite3','.onnx'))
                assert not re.search(rb'sk-(?:proj-)?[A-Za-z0-9_-]{40,}', archive.read(name)), 'Credential-shaped value in archive'
            for name, digest in report['source_sha256'].items():
                assert hashlib.sha256(archive.read(name.replace('\\','/'))).hexdigest() == digest
            if filename == 'restored-source.zip':
                assert set(archive.namelist()) == set(package['files_sha256'])
                assert all(hashlib.sha256(archive.read(n)).hexdigest() == d for n,d in package['files_sha256'].items())
                assert 'apps/elia/LICENSE' in archive.namelist()

    video = ROOT/'assets/demo'/manifest['video']
    decode = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v','error','-i',str(video),
        '-map','0:v:0','-progress','pipe:1','-nostats','-f','null','-'], capture_output=True, text=True, check=True)
    assert not decode.stderr.strip(), decode.stderr
    assert 'progress=end' in decode.stdout
    frames = int(re.findall(r'^frame=(\d+)', decode.stdout, re.M)[-1])
    duration = int(re.findall(r'^out_time_us=(\d+)', decode.stdout, re.M)[-1]) / 1e6
    assert frames == 1013 and abs(duration - 67.533333) < .1
    tracked = ['index.html','supplement.html','article.css','article-tokens.css','article.js','data/answers.json','data/study-summary.json',
        'data/route-comparison.json','data/paired-routes.json','evidence/analyse_study.py',
        'evidence/verify_article.py','evidence/PROVENANCE.md','evidence/figure-style.json','evidence/figure-manifest.json',
        'evidence/build_publication_figures.py','evidence/system_figures.py','evidence/architecture_plate.py','data/system-trace.json','data/energy-comparison.json','evidence/publication-figures.json']
    result = {'passed':True, 'checked_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Local file/data integrity and complete video decode; browser checks recorded separately.',
        'relative_targets':len(linked), 'publication_figures':10, 'questions':60, 'responses':180, 'routing_decisions':len(rows),
        'native_capture_pngs':len(seen), 'decoded_frames':frames, 'decoded_duration_s':duration,
        'article_sha256':{n:sha(ROOT/n) for n in tracked}}
    (ROOT/'evidence/validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'article_sha256'},indent=2))

if __name__ == '__main__': main()
