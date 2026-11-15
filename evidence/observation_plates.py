"""Authored scientific plates. Geometry encodes only retained observations.

Shared palette and Poppins typography match the accepted system architecture.
Mobile layouts rearrange panels without altering text, quantities or samples.
"""
import ast
import csv
import json
import numpy as np


class Plate:
    def __init__(self, node):
        self.node = node
        self.b = ''

    def text(self, x, y, s, size=12, col='ink', w=None, center=True):
        self.b += self.node(x-w/2 if w and center else x, y, s, size, col,
                            width=w, align='center' if center else 'left',
                            extra='anchor=north' if center and not w else '')

    def area(self, x, y, w, h, fill='group', radius=8):
        self.b += f'\\path[fill={fill},rounded corners={radius}pt] ({x},{y}) rectangle ({x+w},{y+h});\n'

    def line(self, points, col='ink', arrow=True, dashed=False):
        self.b += '\\draw['+('-{Stealth[length=4pt,width=3pt]},' if arrow else '')+f'draw={col},line width=.7pt'+(',dashed' if dashed else '')+'] '+' -- '.join(f'({x},{y})' for x,y in points)+';\n'

    def sheet(self, x, y, w, h, fill='white'):
        self.b += f'\\path[fill={fill},draw=line,line width=.6pt] ({x},{y}) -- ({x+w-10},{y}) -- ({x+w},{y+10}) -- ({x+w},{y+h}) -- ({x},{y+h}) -- cycle;\n'
        self.line([(x+w-10,y),(x+w-10,y+10),(x+w,y+10)],'line',False)

    def band(self, x, y, w, h, text, fill='mint', size=12):
        self.area(x,y,w,h,fill,3)
        self.text(x+w/2,y+(h-size*1.5)/2,text,size,w=w-8)


def routing(node, doc, mobile):
    p=Plate(node);w,h=(350,675) if mobile else (1020,390)
    p.text(w/2,12,'Explain whether a triangle has three sides.',13,w=w-32)
    for i in range(2):
        x,y,pw=(16,73+i*279,318) if mobile else (30+i*505,62,455)
        col,fill=('api','peachplane') if i==0 else ('local','blueplane')
        p.text(x+pw/2,y,r'\textbf{'+('(a) Original: substring' if i==0 else '(b) Restored: complete word')+'}',13)
        p.area(x,y+34,pw,143)
        cw=29;left=x+(pw-7*cw)/2
        for j,c in enumerate('whether'):
            p.area(left+j*cw,y+57,cw-2,39,fill if 2<=j<=4 else 'white',2)
            p.text(left+j*cw+(cw-2)/2,y+61,c,22)
        if i==0:
            p.line([(left+2*cw,y+108),(left+5*cw-2,y+108)],col,False)
            p.text(x+pw/2,y+119,'eth is present inside whether',11,col)
        else:
            for bx in [left-8,left+7*cw+6]:
                p.line([(bx,y+51),(bx,y+102)],col,False,True)
            p.text(x+pw/2,y+119,'The complete word is whether, not eth',10.7,col)
        p.text(x+pw/2,y+148,'Real-time keyword predicate',10.5,'muted')
        p.line([(x+pw/2,y+177),(x+pw/2,y+202)],col)
        p.band(x+pw/2-52,y+204,104,27,'true' if i==0 else 'false',fill)
        p.line([(x+pw/2,y+231),(x+pw/2,y+249)],col)
        p.text(x+pw/2,y+253,r'API\_CHECK' if i==0 else 'LOCAL',15,col)
    if not mobile:
        p.line([(510,68),(510,345)],'line',False)
    p.text(w/2,h-27,'Same sentence · actual initial decisions',10.5,'muted')
    return doc(p.b,w,h)


def answer(node, doc, escape, example, root, mobile):
    p=Plate(node);w,h=(350,889) if mobile else (1020,400)
    p.text(w/2,12,escape(example['question']),12.7,w=w-40)
    # Exact complete response occupies an explicit, independently checked region.
    x,y,pw=(16,119,318) if mobile else (26,97,367)
    p.text(x+pw/2,y,r'\textbf{(a) Recorded local reply}',13)
    p.sheet(x,y+32,pw,187 if mobile else 162)
    response=escape(example['answers'][0]['response']).replace('\n\n',r'\par\vspace{9pt}').replace('\n',r'\\')
    p.text(x+15,y+49,response,12.3,w=pw-30,center=False)
    # Return PDF-point clip via manifest; TeX pt -> PDF bp conversion is explicit.
    clip=[x,y+34,x+pw,y+(217 if mobile else 192)]
    p.text(x+pw/2,y+(232 if mobile else 224),'Last number: 621 · reference: 193',11,'api')
    x,y,pw=(16,404,318) if mobile else (426,97,278)
    p.text(x+pw/2,y,r'\textbf{(b) Reference quantities}',13)
    p.text(x+pw/2,y+39,'600 newspapers in total',12)
    bx,by,bw=x+5,y+89,pw-10
    for value,label,fill in [(198,'A','blueplane'),(193,'B','mint'),(209,'C','operation')]:
        width=bw*value/600
        p.area(bx,by,width,51,fill,0)
        p.text(bx+width/2,by+8,label,11)
        p.text(bx+width/2,by+26,str(value),13)
        bx+=width
    p.text(x+pw/2,y+158,'600 − 198 − 209 = 193',15,'local')
    p.text(x+pw/2,y+200,'Reference arithmetic; not model reasoning',10.3,'muted',w=pw)
    x,y,pw=(16,666,318) if mobile else (744,97,250)
    p.text(x+pw/2,y,r'\textbf{(c) Escalation predicate}',13)
    source=(root/'evidence/results/2026-11-12/source/heuristics.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    phrases=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UNCERTAINTY_PHRASES' for t in n.targets))
    assert len(phrases)==4
    assert not any(s in example['answers'][0]['response'].lower() for s in phrases)
    p.area(x,y+34,pw,132)
    for j,s in enumerate(phrases):
        p.text(x+13,y+44+j*28,escape(s),11.4,center=False)
        p.band(x+pw-53,y+42+j*28,39,22,'false','operation',9.5)
    p.line([(x+pw/2,y+166),(x+pw/2,y+187)])
    p.band(x+18,y+189,pw-36,31,'No phrase: no escalation','blueplane',11)
    if not mobile:
        for xx in [411,724]:p.line([(xx,103),(xx,355)],'line',False)
    return doc(p.b,w,h),[v*72/72.27 for v in clip]


def comparison(node, doc, data, mobile):
    p=Plate(node);w,h=(350,690) if mobile else (1020,390)
    case=data['cases'][0]
    x,y,pw=(16,14,318) if mobile else (28,14,385)
    p.text(x+pw/2,y,r'\textbf{(a) Same estimator input}',14)
    p.sheet(x+36,y+40,pw-72,62,'mint')
    p.text(x+pw/2,y+49,'France reply · n = 62',13)
    p.text(x+pw/2,y+76,'Same 62-token estimator input',10.5,'muted')
    p.line([(x+pw/2,y+102),(x+pw/2,y+125)],arrow=False)
    for j,(col,fill,coefficient,title) in enumerate([
            ('local','blueplane','0.85','Local profile'),('cloud','purpleplane','3.10','GPT-4o proxy')]):
        cx=x+pw*(.25+.5*j)
        p.line([(x+pw/2,y+125),(cx,y+125),(cx,y+148)],col)
        p.band(cx-64,y+150,128,39,coefficient+' J/token',fill,12.5)
        p.text(cx,y+199,title,11,col)
    p.area(x+17,y+237,pw-34,75,'group')
    p.text(x+pw/2,y+249,'E = n × c / 3,600 (Wh)',14)
    p.text(x+pw/2,y+278,'Configured estimate',11,'muted')
    x,y,pw=(16,368,318) if mobile else (470,14,519)
    p.text(x+pw/2,y,r'\textbf{(b) Profile comparison}',14)
    left=x+(59 if mobile else 94);right=x+pw-25;scale=(right-left)/65
    for j,(col,fill,title,value,bounds) in enumerate([
        ('local','blueplane','Local',case['local_mwh'],case['local_range_mwh']),
        ('cloud','purpleplane','Cloud proxy',case['cloud_proxy_mwh'],case['cloud_proxy_range_mwh'])]):
        yy=y+80+j*94
        p.text(left,yy-30,title,11,col,center=False)
        p.area(left,yy,value*scale,28,fill,0)
        low,high=[left+v*scale for v in bounds]
        p.line([(low,yy+14),(high,yy+14)],col,False)
        for xx in [low,high]:p.line([(xx,yy+8),(xx,yy+20)],col,False)
        p.text(left+value*scale+6,yy-4,f'{value:.1f}',13,col,center=False)
    yy=y+232
    p.line([(left,yy),(right,yy)],'muted',False)
    for value in [0,20,40,60]:
        xx=left+value*scale;p.line([(xx,yy),(xx,yy+5)],'muted',False);p.text(xx,yy+12,str(value),10.5,'muted')
    p.text((left+right)/2,yy+38,'Estimated energy (mWh)',11)
    p.text(x+pw/2,y+304,'Whiskers: configured coefficient bounds',10.5,'muted')
    if not mobile:p.line([(441,28),(441,343)],'line',False)
    return doc(p.b,w,h)


def axis(points, x, y, w, h, xmin, xmax, ymax, xticks, shades):
    b=r'\begin{axis}['+f'at={{({x}pt,-{y}pt)}},anchor=north west,width={w}pt,height={h}pt,scale only axis,'+r'''
axis lines=left,axis line style={line width=.5pt,draw=muted},
tick style={line width=.5pt,draw=muted},tick label style={font=\fontsize{10}{15}\selectfont,text=muted},
xticklabel={\pgfmathprintnumber[assume math mode=true]{\tick}},
yticklabel={\pgfmathprintnumber[assume math mode=true]{\tick}},
ymajorgrids=true,grid style={line width=.3pt,draw=line,dashed},
'''+f'xmin={xmin},xmax={xmax},ymin=0,ymax={ymax},xtick={{{xticks}}},ytick={{0,20,40}},clip=true]\n'
    for left,right,label in shades:
        b+=f'\\path[fill=mint] (axis cs:{left},0) rectangle (axis cs:{right},{ymax});\n'
        if label:b+=f'\\node[anchor=north,font=\\fontsize{{10.5}}{{15}}\\selectfont,text=ink] at (axis cs:{(left+right)/2},{ymax-1}) {{{label}}};\n'
    b+=r'\addplot[local,line width=1pt,no marks] coordinates {'+' '.join(f'({a:.6f},{v:.6f})' for a,v in points)+'};\n'
    return b+r'\end{axis}'+'\n'


def power(node, doc, run, sources, mobile):
    summary,rows,t,values=run
    phase=next(v for v in summary['phases'] if v['kind']=='inference')
    origin=phase['start_ms']/1000;duration=phase['duration_s']
    selected=(t>=origin-20)&(t<=origin+duration+20)
    points=list(zip(t[selected]-origin,values[selected]))
    with (sources/'power-interval.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.writer(f);wr.writerow(['seconds','watts']);wr.writerows(points)
    p=Plate(node);w,h=(350,665) if mobile else (1020,390)
    x,y,pw=(16,14,318) if mobile else (26,14,653)
    p.text(x+pw/2,y,r'\textbf{(a) Whole-laptop discharge}',14)
    p.text(x+33,y+38,'Power (W)',11,'muted',center=False)
    px,py,aw,ah=x+35,y+76,pw-53,193 if mobile else 203
    p.b+=axis(points,px,py,aw,ah,-20,duration+20,42,'0,30,60,90,120',[(0,duration,'20 local questions')])
    p.text(px+aw/2,py+ah+34,'Time from first request (s)',11)
    x,y,pw=(16,387,318) if mobile else (722,14,272)
    p.text(x+pw/2,y,r'\textbf{(b) Integrated interval}',14)
    p.area(x,y+48,pw,117,'mint')
    p.text(x+pw/2,y+61,f"{phase['whole_laptop_wh']:.3f} Wh",28,'local')
    p.text(x+pw/2,y+109,f'{duration:.1f} s · 20 requests',12)
    p.text(x+pw/2,y+139,'Trapezoidal integral of raw samples',10,'muted')
    p.area(x,y+186,pw,74,'group')
    p.text(x+pw/2,y+195,'Screen + OS + active applications',11,w=pw-20)
    p.text(x+pw/2,y+226,'Loaded-idle power not subtracted',10.5,'muted')
    if not mobile:p.line([(701,28),(701,342)],'line',False)
    return doc(p.b,w,h),phase


def battery(node, doc, runs, sources, mobile):
    p=Plate(node);w,h=(350,810) if mobile else (1020,715)
    xmax=max((t[-1]-t[0])/60 for _,_,t,_ in runs)
    ymax=max(40,np.ceil(max(max(v) for _,_,_,v in runs)/10)*10)
    labels=['Original / plaintext','Template exposed','Revised local prompt']
    for j,(summary,records,t,values) in enumerate(runs):
        top=16+j*(253 if mobile else 221)
        p.text(18,top,r'\textbf{('+chr(97+j)+') '+labels[j]+'}',12.5,center=False)
        if mobile:
            p.text(18,top+26,f"{summary['inference_wh']:.3f} Wh over {summary['inference_duration_s']:.1f} s",10.5,'local',center=False)
        else:
            p.text(740,top,f"{summary['inference_wh']:.3f} Wh over {summary['inference_duration_s']:.1f} s",11,'local',center=False)
        p.text(48,top+(51 if mobile else 27),'Power (W)',10.5,'muted',center=False)
        points=list(zip((t-t[0])/60,values))
        shades=[((s['start_ms']/1000-t[0])/60,(s['end_ms']/1000-t[0])/60,str(s['block'])) for s in summary['phases'] if s['kind']=='inference']
        p.b+=axis(points,48,top+(80 if mobile else 57),w-74,126,0,xmax,ymax,'0,2,4,6,8,10,12',shades)
        with (sources/f"battery-{summary['id']}.csv").open('w',newline='',encoding='utf-8') as f:
            wr=csv.writer(f);wr.writerow(['minutes','watts']);wr.writerows(points)
        p.text(w/2,top+(229 if mobile else 202),'Elapsed time (min)',10.5)
    p.text(w/2,h-27,'Shaded: inference blocks 1–3 · same axes throughout',10.5,'muted',w=w-24)
    return doc(p.b,w,h)
