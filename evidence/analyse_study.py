"""Validate three preserved runs and plot recorded observations, without inference."""
from __future__ import annotations
import csv
import json
import hashlib
import re
import ast
import random
from types import SimpleNamespace
from decimal import Decimal
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parents[1]
for font in (ROOT / 'evidence/fonts').glob('*.ttf'):
    font_manager.fontManager.addfont(str(font))
STYLE = json.loads((ROOT/'evidence/figure-style.json').read_text(encoding='utf-8'))
COLOR = STYLE['colors']
BLUE, PURPLE, RED, GREY = (COLOR[k] for k in ['match','cloud','api','miss'])
CONFIG_COLORS = [c['color'] for c in STYLE['configurations']]
plt.rcParams.update({'font.family': STYLE['sans'], 'font.size': 10,
    'text.color': COLOR['text'], 'axes.labelcolor': COLOR['text'],
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': '#93979a', 'axes.linewidth': .65,
    'xtick.color': COLOR['text'], 'ytick.color': COLOR['text'],
    'xtick.major.width': .65, 'ytick.major.width': .65,
    'axes.titlelocation': 'left', 'axes.titlesize': 11, 'axes.titleweight': 500,
    'axes.titlepad': 16, 'legend.frameon': False, 'svg.fonttype': 'path',
    'pdf.fonttype': 42, 'pdf.use14corefonts': False, 'axes.facecolor': 'none'})


def write_article_tokens():
    lines = ['/* Generated with the figures from evidence/figure-style.json. */']
    for face in STYLE['font_faces']:
        fmt = 'woff2' if face['file'].endswith('.woff2') else 'truetype'
        lines.append('@font-face{font-family:"'+face['family']+'";src:url("evidence/fonts/'+face['file']+
            '") format("'+fmt+'");font-weight:'+str(face['weight'])+';font-style:'+face['style']+';font-display:swap}')
    lines.append(':root{' + ''.join('--'+name+':'+value+';' for name,value in COLOR.items()) +
        '--sans:"'+STYLE['sans']+'","Helvetica Neue",Arial,sans-serif;--serif:"'+STYLE['serif']+'",Georgia,serif;}')
    (ROOT/'article-tokens.css').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def integrate(t, power, start, end):
    a, b = max(start, t[0]), min(end, t[-1])
    if b <= a:
        raise ValueError('No telemetry in phase')
    times = np.r_[a, t[(t > a) & (t < b)], b]
    values = np.interp(times, t, power)
    wh = float(np.trapezoid(values, times) / 3600)
    return {'duration_s': end - start, 'covered_s': b - a,
            'whole_laptop_wh': wh, 'mean_power_w': wh * 3600 / (b - a)}


def load_run(folder, label):
    path = ROOT / 'evidence/results' / folder
    meta = json.loads((path / 'run.json').read_text(encoding='utf-8'))
    rows = [json.loads(x) for x in (path / 'gsm8k-local.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 60 and [r['row'] for r in rows] == meta['rows']
    dataset_path = ROOT / 'evidence/datasets/gsm8k-test.jsonl'
    assert hashlib.sha256(dataset_path.read_bytes()).hexdigest() == meta['dataset_sha256']
    dataset = [json.loads(x) for x in dataset_path.read_text(encoding='utf-8').splitlines()]
    assert meta['rows'] == random.Random(meta['seed']).sample(range(len(dataset)), 60)
    source_dir = path / 'source'
    for name, digest in meta['source_sha256'].items():
        assert hashlib.sha256((source_dir/name).read_bytes()).hexdigest() == digest
    # Execute only the archived uncertainty function and its literal phrase list.
    # No adapters, env files or runtime clients are loaded during analysis.
    tree = ast.parse((source_dir/'heuristics.py').read_text(encoding='utf-8'))
    selected = [n for n in tree.body if
        (isinstance(n, ast.FunctionDef) and n.name == 'response_shows_uncertainty') or
        (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'UNCERTAINTY_PHRASES' for t in n.targets))]
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future]+selected, type_ignores=[])), '<archived-uncertainty>', 'exec'), namespace)
    def number(text):
        values = re.findall(r'-?\d[\d,]*(?:\.\d+)?', text)
        return Decimal(values[-1].replace(',', '')) if values else None
    for row in rows:
        assert row['question'] == dataset[row['row']]['question']
        gold = number(dataset[row['row']]['answer'].split('####')[-1])
        assert Decimal(row['reference']) == gold
        assert row['correct'] == (number(row['response']) == gold)
        assert row['prediction'] == str(number(row['response']))
        assert row['would_escalate'] == namespace['response_shows_uncertainty'](SimpleNamespace(text=row['response']))
    with (path / 'battery.csv').open(encoding='utf-8', newline='') as stream:
        battery = list(csv.DictReader(stream))
    assert all(r['power_online'] == '0' for r in battery), 'AC power connected during run'
    t = np.array([int(r['unix_ms']) / 1000 for r in battery])
    power = np.array([int(r['discharge_mw']) / 1000 for r in battery])
    assert np.all(np.diff(t) > 0) and np.all((power >= 0) & (power < 200))
    phases = [dict(p, **integrate(t, power, p['start_ms']/1000, p['end_ms']/1000)) for p in meta['phases']]
    inference = [p for p in phases if p['kind'] == 'inference']
    assert all(abs(p['duration_s'] - p['covered_s']) < 0.01 for p in inference)
    latency = [r['latency_s'] for r in rows]
    summary = {'id': folder, 'label': label, 'n': len(rows),
        'correct': sum(r['correct'] for r in rows),
        'uncertainty_triggers': sum(r['would_escalate'] for r in rows),
        'wrong_unflagged': sum(not r['correct'] and not r['would_escalate'] for r in rows),
        'correct_flagged': sum(r['correct'] and r['would_escalate'] for r in rows),
        'latency_median_s': float(np.median(latency)), 'latency_p95_s': float(np.percentile(latency,95)),
        'completion_tokens': sum(r['usage'].get('completion_tokens',0) for r in rows),
        'inference_wh': sum(p['whole_laptop_wh'] for p in inference),
        'inference_duration_s': sum(p['duration_s'] for p in inference),
        'battery_samples': len(battery), 'sample_gap_max_s': float(max(np.diff(t))),
        'phases': phases, 'source': f'evidence/results/{folder}/gsm8k-local.jsonl'}
    return summary, rows, t, power


def save(fig, name):
    target = ROOT/'assets/figures'/name
    # Fixed canvases preserve panel alignment; PDF embeds the same TrueType faces.
    fig.savefig(target, facecolor='none', metadata={'Date': None})
    fig.savefig(target.with_suffix('.pdf'), facecolor='none',
        metadata={'CreationDate':None,'ModDate':None,'Creator':'SEVEN reproducible figure source'})
    previews = ROOT/'output/figures'; previews.mkdir(parents=True,exist_ok=True)
    fig.savefig(previews/target.with_suffix('.png').name, dpi=180, facecolor=COLOR['wash'])
    plt.close(fig)


def plot_quality(runs):
    fig, (a,b) = plt.subplots(1,2,figsize=(10.5,5), gridspec_kw={'width_ratios':[1.8,1]})
    for block in range(3):
        for run, (_, rows, _, _) in enumerate(runs):
            subset = rows[block*20:(block+1)*20]
            y = (2-block)*4 + (2-run)
            for i, row in enumerate(subset):
                a.scatter(i+1,y,s=77,marker='s',c=BLUE if row['correct'] else GREY,edgecolors='none')
                if row['would_escalate']:
                    a.scatter(i+1,y,s=115,marker='s',facecolors='none',edgecolors=RED,linewidths=1.3)
            a.text(21.1,y,f"{sum(r['correct'] for r in subset)}/20",va='center',fontsize=9)
    a.set(ylim=(-.8,11.3), xlim=(.3,23.5), xticks=[1,5,10,15,20], xlabel='Question within each block',
          yticks=[10,9,8,6,5,4,2,1,0], yticklabels=['Original','Template','Revised']*3)
    for y, block in [(10,1),(6,2),(2,3)]:
        a.text(.35,y+.67,f'Block {block}',fontsize=9,color=COLOR['muted'])
    a.set_title('(a) The same 60 questions')
    for spine in a.spines.values(): spine.set_visible(False)
    a.tick_params(axis='y',length=0)
    fig.legend(handles=[Patch(color=BLUE,label='Numeric match'),Patch(color=GREY,label='No match'),
        Patch(facecolor='none',edgecolor=RED,label='Uncertainty trigger')],loc='lower left',bbox_to_anchor=(.065,.015),ncol=3,fontsize=9)
    for (summary, rows,_,_), color in zip(runs,CONFIG_COLORS):
        values=np.sort([r['latency_s'] for r in rows])
        b.step(values, np.arange(1,61)/60*100, where='post',color=color,lw=1.7,label=summary['label'])
    b.set(xlabel='Complete response (s)',ylabel='Questions completed (%)',ylim=(0,102),xlim=(0,None))
    b.set_title('(b) Response time')
    b.grid(axis='y',color=COLOR['line'],lw=.55,ls=(0,(3,3)))
    b.legend(loc='lower right',fontsize=8.5,handlelength=2)
    fig.subplots_adjust(left=.095,right=.98,wspace=.36,bottom=.23,top=.87)
    save(fig,'local-results.svg')


def plot_power(runs):
    fig, axes = plt.subplots(1,3,figsize=(10.5,3.7),sharex=True,sharey=True)
    xmax=max((t[-1]-t[0])/60 for _,_,t,_ in runs)
    ymax=max(40, np.ceil(max(max(power) for _,_,_,power in runs)/10)*10)
    for row, ((summary, records,t,power),color) in enumerate(zip(runs,CONFIG_COLORS)):
        ax=axes[row]
        start=t[0]
        for phase in summary['phases']:
            left=(phase['start_ms']/1000-start)/60
            right=(phase['end_ms']/1000-start)/60
            if phase['kind']=='inference':
                ax.axvspan(left,right,color=color,alpha=.10,lw=0)
                ax.text((left+right)/2,.96,str(phase['block']),
                    transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=8.5,color=COLOR['muted'])
        ax.plot((t-start)/60,power,color=color,lw=1.15)
        ax.set(xlim=(0,xmax),ylim=(0,ymax),xlabel='Elapsed time (min)',xticks=np.arange(0,xmax+1,2))
        if row==0: ax.set_ylabel('Battery discharge (W)')
        ax.set_title(f"({chr(97+row)}) {summary['label']}",fontsize=10)
        ax.text(.5,-.48,f"{summary['inference_wh']:.3f} Wh over {summary['inference_duration_s']:.1f} s",
            ha='center',transform=ax.transAxes,fontstyle='italic',fontsize=10)
        ax.grid(axis='y',color=COLOR['line'],lw=.55,ls=(0,(3,3)))
    fig.subplots_adjust(left=.075,right=.985,wspace=.16,bottom=.34,top=.82)
    save(fig,'battery-test.svg')


def plot_routing():
    data=json.loads((ROOT/'data/route-comparison.json').read_text(encoding='utf-8'))
    fig,ax=plt.subplots(figsize=(10.5,4.4))
    routes=['LOCAL','API_CHECK','CLOUD']
    names=['Local model','Live-data check','Cloud model']
    colors=[COLOR[k] for k in ['local','api','cloud']]
    transitions=data['transitions']
    unit=.60/data['n']; gap=.10
    positions=[]
    for version in data['versions']:
        top=.13; nodes={}
        for route in routes:
            nodes[route]=[top,top+version['routes'][route]*unit]
            top=nodes[route][1]+gap
        positions.append(nodes)
    outgoing={r:positions[0][r][0] for r in routes}
    incoming={r:positions[1][r][0] for r in routes}
    # Every ribbon has exactly the same proportional width at both ends.
    # No minimum-width expansion is applied to the two-prompt ribbon.
    for source,color in zip(routes,colors):
        for target in routes:
            count=transitions.get(source+' -> '+target,0)
            if not count:continue
            a,c=outgoing[source],incoming[target]; b,d=a+count*unit,c+count*unit
            vertices=[(.275,a),(.44,a),(.56,c),(.725,c),(.725,d),(.56,d),(.44,b),(.275,b),(.275,a)]
            codes=[MplPath.MOVETO,MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.LINETO,
                   MplPath.CURVE4,MplPath.CURVE4,MplPath.CURVE4,MplPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MplPath(vertices,codes),facecolor=color,alpha=.22,edgecolor='none'))
            if source=='API_CHECK' and target in ['LOCAL','CLOUD']:
                ax.text(.5,(a+b+c+d)/4,f"{count:,} to {'local' if target=='LOCAL' else 'cloud'}",
                    ha='center',va='center',fontsize=10,color=COLOR['text'],
                    bbox={'facecolor':COLOR['wash'],'edgecolor':'none','pad':2.5,'alpha':.95})
            outgoing[source]=b;incoming[target]=d
    for side,(x,align) in enumerate([(.25,'right'),(.75,'left')]):
        for route,name,color in zip(routes,names,colors):
            top,bottom=positions[side][route]
            count=data['versions'][side]['routes'][route]
            ax.add_patch(Rectangle((.26 if side==0 else .725,top),.015,bottom-top,facecolor=color,edgecolor='none'))
            y=(top+bottom)/2
            ax.text(x,y-.014,name,ha=align,va='bottom',fontsize=11,fontweight=500,color=color)
            ax.text(x,y+.014,f'{count:,}  /  {count/data["n"]*100:.1f}%',ha=align,va='top',fontsize=10)
        for route in routes:
            assert abs((outgoing if side==0 else incoming)[route]-positions[side][route][1])<1e-10
    ax.text(.25,.055,'Original classifier',ha='right',fontweight=500,fontsize=11)
    ax.text(.75,.055,'Restored classifier',ha='left',fontweight=500,fontsize=11)
    ax.text(.5,.055,'15,011 identical prompts',ha='center',fontsize=9,color=COLOR['muted'])
    ax.text(.5,1.075,'Also included: 2 cloud-to-local decisions',ha='center',fontsize=9,color=COLOR['muted'])
    ax.set(xlim=(0,1),ylim=(1.12,0));ax.axis('off')
    fig.subplots_adjust(left=.015,right=.985,bottom=.05,top=.98)
    save(fig,'routing-comparison.svg')


def main():
    write_article_tokens()
    runs=[load_run('2026-11-12','Original / plaintext'),load_run('2026-11-12-templated','Template exposed'),load_run('2026-11-12-restored','Revised local prompt')]
    assert all([r['row'] for r in run[1]] == [r['row'] for r in runs[0][1]] for run in runs)
    data={'method':'One stochastic response per question per configuration. Original and template runs use unchanged SEVEN 713203c; revised local prompt uses the archived restoration snapshot. Same seeded sample; no repeated trials or causal improvement claim.',
          'energy_scope':'Battery-reported whole-laptop discharge, with other active work included. No cloud measurement and no model-only energy claim.',
          'runs':[r[0] for r in runs]}
    (ROOT/'data/study-summary.json').write_text(json.dumps(data,indent=2)+'\n')
    examples=[{'row':row['row'],'question':row['question'],'reference':row['reference'],
       'answers':[dict(run[1][i],configuration=run[0]['label'],source=run[0]['source']) for run in runs]} for i,row in enumerate(runs[0][1])]
    (ROOT/'data/answers.json').write_text(json.dumps(examples,indent=2)+'\n')
    plot_quality(runs);plot_power(runs);plot_routing()
    outputs=[ROOT/'assets/figures'/f'{name}.{ext}' for name in ['routing-comparison','local-results','battery-test'] for ext in ['svg','pdf']]
    manifest={'method':'Matplotlib vector paths from validated records; SVG outlines the shared Poppins glyphs, PDF embeds TrueType fonts. No generated bitmap content.',
        'matplotlib':matplotlib.__version__,'numpy':np.__version__,
        'style_sha256':hashlib.sha256((ROOT/'evidence/figure-style.json').read_bytes()).hexdigest(),
        'font_sha256':{f['file']:hashlib.sha256((ROOT/'evidence/fonts'/f['file']).read_bytes()).hexdigest() for f in STYLE['font_faces']},
        'files_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}}
    (ROOT/'evidence/figure-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({r[0]['id']:{k:r[0][k] for k in ['correct','wrong_unflagged','uncertainty_triggers','inference_wh','inference_duration_s','sample_gap_max_s']} for r in runs},indent=2))


if __name__=='__main__':main()
