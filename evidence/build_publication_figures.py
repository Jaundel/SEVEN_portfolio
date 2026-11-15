"""Validate archived observations, then typeset deliberate TikZ/PGFPlots plates.

Run with --tectonic PATH if tectonic is not on PATH. No provider is contacted.
The generated .tex and CSV files are retained as editable figure sources.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import pymupdf as fitz
import numpy as np
from analyse_study import load_run, ROOT, STYLE
from system_figures import comparison_data, plates

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

def routing(mobile):
    w,h=(350,450) if mobile else (760,240)
    b=node(18,16,'Explain whether a triangle has three sides.',14,width=w-36)
    b+=f'\\draw[line,line width=.6pt] (18,{77 if mobile else 55}) -- ({w-18},{77 if mobile else 55});\n'
    for i,(title,expression,result,col) in enumerate([
        ('(a) Original substring rule',r'\texttt{"eth" in lowered}','Live-data check','api'),
        ('(b) Restored word-boundary rule',r'\texttt{(?<!\textbackslash w)eth(?!\textbackslash w)}','Local model','local')]):
        x=18 if mobile else 18+i*385
        y=99+i*178 if mobile else 77
        b+=node(x,y,title,12)
        b+=node(x,y+31,r'wh\textcolor{api}{\textbf{eth}}er' if i==0 else r'\textcolor{muted}{whether}',24)
        if i==0:
            b+=node(x+135,y+41,'Substring found',11,'api')
        else:
            b+=node(x+135,y+41,'No whole-word match',11,'local')
        b+=node(x,y+80,expression,10.8)
        b+=node(x,y+112,result,18,col)
    return doc(b,w,h)

def answer(example,mobile):
    w,h=(350,525) if mobile else (760,325)
    b=node(18,16,escape(example['question']),12.4,width=w-36)
    split=125 if mobile else 104
    b+=f'\\draw[line,line width=.6pt] (18,{split-15}) -- ({w-18},{split-15});\n'
    x,y=18,split
    b+=node(x,y,'(a) Recorded local reply',12,'api')
    # Verbatim complete first response: preserve the model's mistakes.
    response=example['answers'][0]['response']
    b+=node(x,y+34,escape(response).replace('\n\n',r'\par\vspace{9pt}').replace('\n',r'\\'),12.2,width=314 if mobile else 330)
    x2,y2=(18,330) if mobile else (415,split)
    b+=node(x2,y2,'(b) Reference calculation',12,'local')
    b+=node(x2,y2+40,'600 − 198 − 209 = 193',18,'local')
    b+=node(x2,y2+87,'Subtract both delivered quantities\nfrom the total.'.replace('\n',r'\\'),12,width=310)
    b+=node(x2,y2+155,'Uncertainty rule: not triggered',12)
    return doc(b,w,h)

def power(run,mobile):
    summary,rows,t,p=run
    phase=next(p for p in summary['phases'] if p['kind']=='inference')
    origin=phase['start_ms']/1000
    start,end=-20,phase['duration_s']+20
    # Every original battery sample in this window; no smoothing or aggregation.
    selected=(t>=origin+start)&(t<=origin+end)
    with (SOURCES/'power-interval.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.writer(f);wr.writerow(['seconds','watts'])
        wr.writerows(zip(t[selected]-origin,p[selected]))
    points=' '.join(f'({x:.6f},{y:.6f})' for x,y in zip(t[selected]-origin,p[selected]))
    w,h=(350,375) if mobile else (760,350)
    plotw,ploth=(278,180) if mobile else (650,200)
    top=51
    label='Whole-laptop battery discharge (W)'
    b=node(18,12,label,12)
    b+=r'\begin{axis}['+f'at={{(52pt,-{top}pt)}},anchor=north west,width={plotw}pt,height={ploth}pt,scale only axis,'+r'''
axis lines=left,axis line style={line width=.5pt,draw=muted},
tick style={line width=.5pt,draw=muted},tick label style={font=\fontsize{10}{15}\selectfont,text=muted},
xticklabel={\pgfmathprintnumber[assume math mode=true]{\tick}},
yticklabel={\pgfmathprintnumber[assume math mode=true]{\tick}},
xtick={0,30,60,90,120},ytick={0,10,20,30,40},ymin=0,ymax=42,
ymajorgrids=true,grid style={line width=.3pt,draw=line,dashed},
'''+f'xmin={start},xmax={end},'+r'clip=false]'+ '\n'
    dur=phase['duration_s']
    b+=f'\\path[fill=local,fill opacity=.10] (axis cs:0,0) rectangle (axis cs:{dur},42);\n'
    b+=r'\addplot[local,line width=1.1pt,no marks] coordinates {'+points+'};\n'
    for bound in [0,dur]: b+=f'\\draw[local,densely dashed,line width=.55pt] (axis cs:{bound},0) -- (axis cs:{bound},42);\n'
    b+=f'\\node[anchor=north,font=\\fontsize{{11}}{{16}}\\selectfont,text=ink] at (axis cs:{dur/2},40) {{20 local questions}};\n'
    b+=r'\end{axis}'+'\n'
    b+=node(52,top+ploth+30,'Time from first request (s)',11)
    by=top+ploth+65
    b+=node(18,by,f"{phase['whole_laptop_wh']:.3f} Wh over {dur:.1f} s",14,'local')
    if mobile:
        b+=node(18,by+31,'Includes display, OS and other applications.',10.2,'muted',width=314)
    else:
        b+=node(340,by+3,'Display, OS and other applications included',11,'muted')
    return doc(b,w,h),phase

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
    system,comparison=plates(node,doc)
    for mobile in [False,True]:
        ptex,phase=power(run,mobile)
        for name,source in [('system-architecture',system(mobile)),('energy-comparison',comparison(comparison_inputs,mobile)),('routing-rule',routing(mobile)),('answer-case',answer(example,mobile)),('power-interval',ptex)]:
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
                generated.append({'name':name,'width_pt':page.rect.width,'height_pt':page.rect.height})
    files=[p for f in generated for p in [SOURCES/(f['name']+'.tex'),OUT/(f['name']+'.pdf'),OUT/(f['name']+'.svg')]]+[SOURCES/'power-interval.csv']
    manifest={'method':'Validated archived data -> authored TikZ and PGFPlots -> Tectonic PDF -> vector SVG. Poppins embedded in PDF; SVG glyph paths. Mobile and desktop compose the same observations without changing results.',
        'versions':{'tectonic':subprocess.run([args.tectonic,'--version'],capture_output=True,text=True,check=True).stdout.strip(),'pymupdf':fitz.__version__,'numpy':np.__version__},
        'figures':generated,'answer_case':{'row':663,'configuration':'Original / plaintext','selection':'First seeded question, not selected by outcome','complete_response':example['answers'][0]['response']},
        'power_interval':phase,'route_case':pair,'energy_comparison':comparison_inputs,'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),ROOT/'evidence/system_figures.py',ROOT/'data/energy-comparison.json',ROOT/'evidence/demo/report.json',ROOT/'evidence/demo/source-snapshot.zip',ROOT/'evidence/analyse_study.py',ROOT/'data/answers.json',ROOT/'data/paired-routes.json',ROOT/'evidence/results/2026-11-12/battery.csv',ROOT/'evidence/results/2026-11-12/run.json',ROOT/'evidence/results/router-2026-11-14/original-heuristics.py',ROOT/'evidence/results/router-2026-11-14/restored-heuristics.py']},
        'files_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files}}
    for p in [ROOT/'evidence/figure-style.json',*(ROOT/'evidence/fonts').glob('Poppins-*.ttf')]:
        manifest['source_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    (ROOT/'evidence/publication-figures.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figures':generated,'power_wh':phase['whole_laptop_wh'],'sources_validated':True},indent=2))

if __name__=='__main__':main()
