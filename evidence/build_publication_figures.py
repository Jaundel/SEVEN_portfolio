"""Validate archived observations, then typeset deliberate TikZ/PGFPlots plates.

Run with --tectonic PATH if tectonic is not on PATH. No provider is contacted.
The generated .tex and CSV files are retained as editable figure sources.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import pymupdf as fitz
import numpy as np
from analyse_study import load_run, ROOT, STYLE
from system_figures import comparison_data
import observation_plates as plates
from architecture_plate import architecture

SOURCES = ROOT/'evidence/figures'
OUT = ROOT/'assets/figures'
PREVIEW = ROOT/'output/figures'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def escape(s):
    return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}'}.get(c,c) for c in s)

def node(x,y,text,size=12,color='ink',width=None,align='left',extra=''):
    opts=f'anchor=north west,inner sep=0pt,text={color},align={align},font=\\fontsize{{{size}}}{{{size*1.5}}}\\selectfont'
    if width: opts+=f',text width={width}pt'
    if extra: opts+=','+extra
    return f'\\node[{opts}] at ({x},{y}) {{{text}}};\n'

def doc(body,width,height):
    colors='\n'.join(r'\definecolor{'+k+'}{HTML}{'+v[1:]+'}' for k,v in STYLE['colors'].items())
    return r'''\documentclass[tikz,border=0pt]{standalone}
\usepackage{fontspec}
\hyphenpenalty=10000
\exhyphenpenalty=10000
\setmainfont[Path=../fonts/,BoldFont=Poppins-SemiBold.ttf,ItalicFont=Poppins-Italic.ttf]{Poppins-Regular.ttf}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{calc,arrows.meta}
'''+colors+r'''
\begin{document}
\begin{tikzpicture}[x=1pt,y=-1pt]
'''+f'\\path[use as bounding box] (0,0) rectangle ({width},{height});\n'+body+r'''
\end{tikzpicture}
\end{document}
'''

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tectonic',default=shutil.which('tectonic'));args=parser.parse_args()
    if not args.tectonic: parser.error('Pass --tectonic PATH or install Tectonic on PATH')
    for p in [SOURCES,OUT,PREVIEW]: p.mkdir(parents=True,exist_ok=True)
    run=load_run('2026-11-12','Original / plaintext')
    example=json.loads((ROOT/'data/answers.json').read_text(encoding='utf-8'))[0]
    assert example['row']==run[1][0]['row']==663
    assert example['answers'][0]['response']==run[1][0]['response']
    assert not example['answers'][0]['would_escalate'] and example['reference']=='193'
    pair=json.loads((ROOT/'data/paired-routes.json').read_text(encoding='utf-8'))[0]
    assert pair['original']['route']=='API_CHECK' and pair['restored']['route']=='LOCAL'
    original=(ROOT/'evidence/results/router-2026-11-14/original-heuristics.py').read_text(encoding='utf-8')
    restored=(ROOT/'evidence/results/router-2026-11-14/restored-heuristics.py').read_text(encoding='utf-8')
    assert 'keyword in lowered' in original and 'r"(?<!\\w)" + re.escape(phrase) + r"(?!\\w)"' in restored
    generated=[]
    comparison_inputs=comparison_data(ROOT)
    runs=[run,load_run('2026-11-12-templated','Template exposed'),load_run('2026-11-12-restored','Revised local prompt')]
    system=lambda mobile: architecture(node,doc,ROOT,mobile)
    for mobile in [False,True]:
        ptex,phase=plates.power(node,doc,run,SOURCES,mobile)
        atex,answer_clip=plates.answer(node,doc,escape,example,ROOT,mobile)
        for name,source in [('system-architecture',system(mobile)),('energy-comparison',plates.comparison(node,doc,comparison_inputs,mobile)),('routing-rule',plates.routing(node,doc,mobile)),('answer-case',atex),('power-interval',ptex),('battery-test',plates.battery(node,doc,runs,SOURCES,mobile))]:
            name+='-mobile' if mobile else ''
            path=SOURCES/(name+'.tex');path.write_text(source,encoding='utf-8')
            cmd=[args.tectonic,'-X','compile','--outdir',str(OUT),path.name]
            result=subprocess.run(cmd,cwd=SOURCES,capture_output=True,text=True,encoding='utf-8')
            (PREVIEW/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
            if result.returncode: raise RuntimeError(f'{name}: '+result.stderr[-2500:])
            pdf=OUT/(name+'.pdf')
            with fitz.open(pdf) as d:
                assert len(d)==1
                page=d[0]
                assert page.get_text().strip()
                (OUT/(name+'.svg')).write_text(page.get_svg_image(text_as_path=True),encoding='utf-8')
                page.get_pixmap(matrix=fitz.Matrix(1.7,1.7),alpha=False).save(PREVIEW/(name+'.png'))
                generated.append({'name':name,'width_pt':page.rect.width,'height_pt':page.rect.height,**({'verbatim_response_clip':answer_clip} if name.startswith('answer-case') else {})})
    files=[p for f in generated for p in [SOURCES/(f['name']+'.tex'),OUT/(f['name']+'.pdf'),OUT/(f['name']+'.svg')]]+[SOURCES/'power-interval.csv',*SOURCES.glob('battery-*.csv')]
    manifest={'method':'Validated archived data -> authored TikZ and PGFPlots -> Tectonic PDF -> vector SVG. Poppins embedded in PDF; SVG glyph paths. Mobile and desktop compose the same observations without changing results.',
        'versions':{'tectonic':subprocess.run([args.tectonic,'--version'],capture_output=True,text=True,check=True).stdout.strip(),'pymupdf':fitz.__version__,'numpy':np.__version__},
        'figures':generated,'answer_case':{'row':663,'configuration':'Original / plaintext','selection':'First seeded question, not selected by outcome','complete_response':example['answers'][0]['response']},
        'power_interval':phase,'route_case':pair,'energy_comparison':comparison_inputs,'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),ROOT/'evidence/system_figures.py',ROOT/'data/energy-comparison.json',ROOT/'evidence/demo/report.json',ROOT/'evidence/demo/source-snapshot.zip',ROOT/'evidence/analyse_study.py',ROOT/'data/answers.json',ROOT/'data/paired-routes.json',ROOT/'evidence/results/2026-11-12/battery.csv',ROOT/'evidence/results/2026-11-12/run.json',ROOT/'evidence/results/router-2026-11-14/original-heuristics.py',ROOT/'evidence/results/router-2026-11-14/restored-heuristics.py']},
        'files_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files}}
    for p in [ROOT/'evidence/figure-style.json',*(ROOT/'evidence/fonts').glob('Poppins-*.ttf')]:
        manifest['source_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    for p in [ROOT/'evidence/architecture_plate.py',ROOT/'evidence/observation_plates.py',ROOT/'data/system-trace.json',ROOT/'evidence/model/genai_config.json',ROOT/'evidence/model/source.json']:
        manifest['source_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    for run_id in ['2026-11-12','2026-11-12-templated','2026-11-12-restored']:
        for filename in ['battery.csv','run.json']:
            p=ROOT/'evidence/results'/run_id/filename
            manifest['source_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    p=ROOT/'evidence/results/2026-11-12/source/heuristics.py'
    manifest['source_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    (ROOT/'evidence/publication-figures.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figures':generated,'power_wh':phase['whole_laptop_wh'],'sources_validated':True},indent=2))

if __name__=='__main__':main()
