"""A three-panel scientific plate: system, local expansion, retained reply.

The repeated planes in (b) denote the 16 decoder layers in the pinned model
configuration. Message sheets, predicate values and saved fields correspond to
application data; there are no decorative neural graphs or invented results.
"""
import hashlib
import json
import ast
import types
import zipfile
from pathlib import Path


def architecture(node,doc,root,mobile=False):
    report=json.loads((root/'evidence/demo/report.json').read_text(encoding='utf-8'))
    case=next(r for r in report['results'] if r['case']=='local-answer')
    assert case['prompt']=='What is the capital of France?'
    assert case['text']=='The capital of France is Paris.'
    config_path=root/'evidence/model/genai_config.json'
    config=json.loads(config_path.read_bytes())
    source=json.loads((root/'evidence/model/source.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(config_path.read_bytes()).hexdigest()==source['sha256']
    assert config['model']['decoder']['num_hidden_layers']==16
    assert config['model']['decoder']['hidden_size']==2048
    # Execute the captured classifier unchanged apart from its annotation-only
    # local-model import. This does not contact a model or provider.
    with zipfile.ZipFile(root/'evidence/demo/source-snapshot.zip') as archive:
        classifier=archive.read('SEVEN/heuristics.py')
    hashes={k.replace('\\','/'):v for k,v in report['source_sha256'].items()}
    assert hashlib.sha256(classifier).hexdigest()==hashes['SEVEN/heuristics.py']
    tree=ast.parse(classifier)
    for i,statement in enumerate(tree.body):
        if isinstance(statement,ast.Try) and any(isinstance(n,ast.ImportFrom) and n.module=='local_model' for n in ast.walk(statement)):
            tree.body[i]=ast.parse('LocalModelResponse = object').body[0]
    scope={};exec(compile(ast.fix_missing_locations(tree),'captured/heuristics.py','exec'),scope)
    q=case['prompt'];match=scope['matches_phrase']
    predicates=[any(match(q,k) for k in scope[name]) for name in ['REALTIME_KEYWORDS','SPECIALIZED_DOMAINS','COMPLEX_MARKERS']]
    predicates.append(len(q.split())>scope['MAX_LOCAL_WORD_COUNT'])
    decision=scope['classify_query_type'](q)
    uncertain=scope['response_shows_uncertainty'](types.SimpleNamespace(text=case['text']))
    assert predicates==[False]*4 and decision['route']=='LOCAL' and uncertain is False
    trace={'prompt':q,'predicates':predicates,'word_count':len(q.split()),'decision':decision,'uncertainty_triggered':uncertain,
        'reply':case['text'],'metadata':case['metadata'],'classifier_sha256':hashes['SEVEN/heuristics.py'],
        'execution':'Captured classifier; only annotation import replaced by object. No function body changed; no provider called.'}
    (root/'data/system-trace.json').write_text(json.dumps(trace,indent=2)+'\n',encoding='utf-8')

    def text(x,y,s,size=12,color='ink',w=None,align='center',extra=''):
        # All operator labels are centred. Descriptive prose stays in captions.
        if w is None:
            return node(x,y,s,size,color,extra='anchor=north'+(','+extra if extra else ''))
        return node(x-w/2,y,s,size,color,width=w,align=align,extra=extra)

    def area(x,y,w,h,fill='group',radius=9,draw='none'):
        return f'\\path[fill={fill},draw={draw},line width=.6pt,rounded corners={radius}pt] ({x},{y}) rectangle ({x+w},{y+h});\n'

    def line(points,col='ink',dashed=False,thick=.8,arrow=True):
        return '\\draw['+('-{Stealth[length=4pt,width=3pt]},' if arrow else '')+f'line width={thick}pt,draw={col}'+(',dashed' if dashed else '')+'] '+' -- '.join(f'({x},{y})' for x,y in points)+';\n'

    def op(x,y,w,h,s,fill='operation',size=12):
        return area(x,y,w,h,fill,3)+text(x+w/2,y+(h-size*1.35*(s.count(r'\\')+1))/2,s,size,w=w-10)

    def sheet(x,y,w,h,col='mint',label=None):
        # Folded-corner sheet denotes an actual message/record, not an operator.
        b=f'\\path[fill={col},draw={col}!65!ink,line width=.55pt] ({x},{y}) -- ({x+w-10},{y}) -- ({x+w},{y+10}) -- ({x+w},{y+h}) -- ({x},{y+h}) -- cycle;\n'
        b+=f'\\draw[{col}!65!ink,line width=.45pt] ({x+w-10},{y}) -- ({x+w-10},{y+10}) -- ({x+w},{y+10});\n'
        if label:b+=text(x+w/2,y+6,label,10)
        return b

    def marker(x,y,label,color='local'):
        return f'\\fill[{color}] ({x},{y}) circle (8pt);\n'+text(x,y-6,r'\textbf{'+label+'}',9,'white')

    b=r'''\definecolor{group}{HTML}{DCE2E5}
\definecolor{operation}{HTML}{C5CFD5}
\definecolor{mint}{HTML}{C9EEDF}
\definecolor{blueplane}{HTML}{AEC8E0}
\definecolor{pinkplane}{HTML}{F6D5DE}
\definecolor{peachplane}{HTML}{FFDBB8}
\definecolor{purpleplane}{HTML}{DCC7E7}
'''
    # (a) A compact overview. The recorded local trace is emphasized; live
    # tools and cloud remain explicit implemented alternatives.
    b+=text(204,12,r'\textbf{(a) Routing and execution}',14)
    b+=sheet(35,51,338,59,'mint')
    b+=text(204,62,case['prompt'],13,w=310)
    b+=text(204,88,'User message q',10.5)
    b+=line([(204,110),(204,138)],'local',thick=1.2)
    b+=area(35,138,338,113,'group')
    b+=text(204,149,'Pre-inference predicates',12.5)
    labels=['Live data','Domain','Complexity','>150 words']
    for i,label in enumerate(labels):
        x=51+i*79
        b+=op(x,183,68,24,str(predicates[i]).lower(),'operation',10.5)
        b+=text(x+34,216,label,9.7)
    b+=text(204,235,'No match: local default',10.7,'local')
    b+=line([(204,251),(204,270)],arrow=False)
    b+=line([(204,270),(77,270),(77,318)],'local',thick=1.3)
    b+=line([(204,270),(204,318)],'api')
    b+=line([(204,270),(331,270),(331,318)],'cloud')
    b+=text(77,285,'LOCAL',10.5,'local')
    b+=text(204,285,'API',10.5,'api')
    b+=text(331,285,'CLOUD',10.5,'cloud')
    # Solid coloured modules: computation. Overlaid planes: repeated/layered
    # data structures, matching the grammar of the supplied research figures.
    b+=area(32,324,90,49,'blueplane',3)
    b+=text(77,331,r'Local\\adapter',12,w=80)
    b+=marker(116,320,'b')
    for i,name in enumerate(['Open-Meteo','Coinbase','BBC']):b+=op(153,319+i*23,102,21,name,'peachplane',10.8)
    b+=op(285,324,92,49,'GPT-4o-mini','purpleplane',10.8)
    b+=line([(373,80),(391,80),(391,349),(377,349)],'cloud')
    b+=text(398,229,'forced cloud',9,'cloud',extra='rotate=90')
    # Escalation uses a reserved channel above the modules.
    b+=line([(122,349),(137,349),(137,307),(271,307),(271,349),(285,349)],'cloud',True)
    b+=text(162,305,'escalate',8.7,'cloud',extra='fill=white,inner sep=1pt')
    # Replies are merged only after the three independent execution paths.
    b+=line([(77,373),(77,424)],'local')
    b+=line([(255,352),(263,352),(263,424)],'api')
    b+=line([(331,373),(331,424)],'cloud')
    b+=line([(77,424),(331,424)],arrow=False)
    b+=line([(204,424),(204,455)])
    b+=sheet(75,455,258,65,'white')
    b+=text(204,467,'R = (text, usage, latency, route)',11.5)
    b+=text(204,493,'Normalized reply',11)
    b+=marker(327,457,'c')
    b+=text(204,548,'Blue trace: recorded France request',10,'local')

    # (b) Actual local adapter and model-serving decomposition. This is an
    # expansion of one component, not an attribution of model design to SEVEN.
    b+='\\draw[line,line width=.65pt] (420,42) -- (420,556);\n'
    b+=text(568,12,r'\textbf{(b) Local path}',14)
    b+=area(445,53,247,350,'group')
    b+=text(568,64,'Ryzen AI server',12.5)
    b+=text(568,86,'Hybrid NPU + iGPU',10.8,'local')
    b+=op(477,112,183,30,'Decode next token','mint',12)
    b+=line([(568,169),(568,142)])
    # These three offset planes stand for the repeated decoder module; the
    # multiplicity is explicit and checked against the actual model config.
    for off in [12,6,0]:b+=area(477+off,181-off,183,65,'operation',4)
    b+=text(568,193,'Decoder layer',13)
    b+=text(568,219,'Hidden width 2,048',10.5)
    b+=text(676,203,'×16',11)
    b+=line([(568,275),(568,246)])
    b+=op(477,275,183,28,'Token embedding','blueplane',12)
    b+=line([(568,326),(568,303)])
    # Token cells carry symbolic indices, not fabricated token IDs.
    for i,s in enumerate([r't\textsubscript{1}',r't\textsubscript{2}',r't\textsubscript{3}','…',r't\textsubscript{T}']):b+=op(483+i*35,326,31,24,s,'blueplane',10.8)
    b+=text(568,357,r'input\_ids',10.8)
    b+=op(477,373,183,25,'Serialize + tokenize','mint',11.5)
    b+=line([(477,385),(464,385),(464,338),(483,338)])
    b+=line([(568,426),(568,398)])
    b+=text(504,407,'HTTP messages[]',9.8,'muted')
    # The adapter sends exactly two role/content messages in this example.
    b+=sheet(459,426,219,47,'mint','system')
    b+=text(568,448,r'Answer accurately and concisely\ldots',10.3,w=200)
    b+=sheet(459,481,219,62,'mint','user')
    b+=text(568,503,case['prompt'],11,w=195)
    b+=text(568,548,'Pretrained Llama 3.2 1B',10.5)
    # Output tokens are fed back during autoregressive decoding.
    b+=line([(660,126),(703,126),(703,291),(660,291)],'local',True)
    b+=text(697,310,'next token',8.8,'local',extra='rotate=90')

    # (c) Source-checked values from the saved response. The text is exact;
    # the token count is reconstructed, as disclosed in the article methods.
    b+='\\draw[line,line width=.65pt] (720,42) -- (720,556);\n'
    b+=text(870,12,r'\textbf{(c) Reply and accounting}',14)
    b+=sheet(747,53,246,86,'white')
    b+=text(870,65,case['text'],12.4,w=218)
    b+=text(870,108,'local · 1.468 s',10.5,'local')
    b+=line([(870,139),(870,166)])
    b+=area(747,166,246,164,'purpleplane!40!white')
    b+=text(870,177,'Configured energy profiles',12)
    b+=text(870,207,'n = 62',13)
    b+=line([(870,231),(870,250)])
    b+=op(757,250,110,31,r'0.85 J/token','blueplane',11)
    b+=op(875,250,108,31,r'3.10 J/token','purpleplane',11)
    b+=text(812,288,'local',10,'local')
    b+=text(929,288,'cloud proxy',10,'cloud')
    b+=text(870,309,'E = n × c / 3,600 (Wh)',11)
    b+=line([(870,330),(870,352)])
    # A record table, rather than another conceptual prose box.
    b+=sheet(747,352,246,114,'white')
    fields=[('route','local'),('model','llama-model'),('estimate','14.6 mWh'),('vs profile','38.8 mWh')]
    for i,(key,value) in enumerate(fields):
        y=361+i*24
        b+=area(754,y,231,22,'wash' if i%2==0 else 'white',0)
        b+=node(762,y+3,key,10.8)
        b+=node(974,y+3,value,10.8,'local' if i in [0,2] else 'ink',extra='anchor=north east')
    b+=line([(870,466),(870,488)])
    # Conventional database cylinder: the persistent SQLite record store.
    b+='\\path[fill=operation] (819,499) -- (819,527) arc[start angle=180,end angle=360,x radius=51pt,y radius=9pt] -- (921,499) -- cycle;\n'
    b+='\\draw[muted,line width=.6pt] (819,499) -- (819,527) arc[start angle=180,end angle=360,x radius=51pt,y radius=9pt] -- (921,499);\n'
    b+='\\path[fill=group,draw=muted,line width=.6pt] (870,499) ellipse[x radius=51pt,y radius=9pt];\n'
    b+=text(870,509,'SQLite',11.5)
    b+=text(870,548,'Saved answer + provenance',10.5)
    # Both exports retain the same scientific composition. The article offers
    # the PDF at full size, rather than turning this plate into a tall flowchart.
    return doc(b,1020,575)
