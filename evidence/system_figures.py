"""Manually composed system plate and an executed, archived-estimator comparison."""
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


def plates(node, doc):
    def rect(x,y,w,h,color='line',fill='white',radius=4,dashed=False):
        return f'\\path[draw={color},fill={fill},line width=.65pt,rounded corners={radius}pt'+(',dashed' if dashed else '')+f'] ({x},{y}) rectangle ({x+w},{y+h});\n'

    def arrow(points,color='muted',dash=False):
        return '\\draw[-{Stealth[length=4pt,width=3.3pt]},line width=.85pt,draw='+color+(',dashed' if dash else '')+'] '+ ' -- '.join(f'({x},{y})' for x,y in points)+';\n'

    def label(x,y,text,col='ink',size=12,width=None):
        return node(x,y,text,size,col,width=width)

    def block(x,y,w,h,title,sub,col):
        b=rect(x,y,w,h,col,col+'!10!white')
        b+=label(x+11,y+9,title,col,12)
        if sub:b+=label(x+11,y+31,sub,'text',10.5,width=w-22)
        return b

    def system(mobile):
        if mobile:
            w,h=350,1020
            b=label(14,12,r'\textbf{I. Request execution}',size=13)
            b+=block(52,48,246,57,'Terminal input','Prompt + optional forced-cloud mode','ink')
            b+=arrow([(175,105),(175,133)])
            b+=block(52,133,246,67,'Ordered routing rules',r'Live data $\rightarrow$ domain / complexity\\ $\rightarrow$ length >150 words $\rightarrow$ local default','ink')
            # Three named routes enter real execution blocks. The right rail
            # collects replies; the left rail carries conditional escalation.
            b+=arrow([(175,200),(175,232)],'local')
            b+=block(52,232,246,79,'Llama 3.2 1B','System + user prompt\\\\Ryzen AI server · NPU + iGPU','local')
            b+=arrow([(175,311),(175,337)],'local')
            b+=block(52,337,246,56,'Uncertainty phrase check','Four substring phrases · no quality model','local')
            b+=arrow([(298,365),(329,365),(329,650),(278,650)],'local')
            b+=label(301,402,'reply','local',9)
            b+=arrow([(52,170),(23,170),(23,451),(52,451)],'api')
            b+=block(52,423,246,75,'Direct live-data tools','Open-Meteo · Coinbase · BBC\\\\Source + timestamp; no LLM rewrite','api')
            b+=arrow([(298,461),(329,461)],'api')
            b+=arrow([(52,186),(12,186),(12,565),(52,565)],'cloud')
            b+=block(52,532,246,75,'GPT-4o-mini','Cloud adapter\\\\Domain / complexity or forced mode','cloud')
            b+=arrow([(52,365),(36,365),(36,565),(52,565)],'cloud',True)
            b+=label(54,402,r'Uncertain / local error $\rightarrow$ cloud','cloud',9)
            b+=arrow([(298,570),(329,570)],'cloud')
            b+=block(52,629,226,66,'Terminal reply + SQLite','Text · source · model · latency\\\\Configured energy metadata','ink')
            b+=label(14,732,r'\textbf{II. Energy bookkeeping}',size=13)
            b+=label(14,766,r'Provider usage n $\rightarrow$ configured profile c',size=11.5)
            b+=rect(14,800,322,57,'line','tint!45!white')
            b+=label(28,814,'Estimate (Wh) = n × c / 3,600',size=14)
            b+=label(14,880,'Local reply: local estimate + cloud-profile baseline.\\\\Escalation: add completed local and cloud estimates.\\\\Direct tools: no inference estimate assigned.',size=11,width=322)
            b+=label(14,968,r'Solid: execution / reply \quad Dashed: conditional fallback',size=9.5)
            return doc(b,w,h)

        w,h=980,648
        b=label(18,12,r'\textbf{I. SEVEN execution paths}',size=14)
        b+=label(732,12,r'\textbf{II. Routing order}',size=14)
        b+='\\draw[line,line width=.6pt] (710,12) -- (710,625);\n'
        b+=block(26,62,151,63,'Terminal input','Prompt + mode','ink')
        b+=arrow([(100,62),(100,43),(690,43),(690,260),(670,260)],'cloud')
        b+=label(518,22,'Forced cloud mode','cloud',10)
        b+=arrow([(177,93),(215,93)])
        b+=block(215,62,263,63,'Pre-inference rules','Whole-word / phrase predicates','ink')
        b+=arrow([(346,125),(346,159),(126,159),(126,203)],'local')
        b+=arrow([(346,125),(346,203)],'api')
        b+=arrow([(346,125),(346,159),(566,159),(566,203)],'cloud')
        b+=label(41,172,'Default','local',11)
        b+=label(279,172,'Current facts','api',11)
        b+=label(502,172,'Complex / domain','cloud',11)
        b+=rect(24,203,204,254,'local','local!7!white')
        b+=label(36,215,r'\textbf{Local inference}','local',13)
        b+=label(36,239,'On this laptop','muted',10.5)
        b+=block(38,270,176,49,'Prompt construction','System + user messages','local')
        b+=arrow([(126,319),(126,338)],'local')
        b+=block(38,338,176,61,'Llama 3.2 1B','Ryzen AI server\\\\NPU + iGPU','local')
        b+=arrow([(126,399),(126,418)],'local')
        b+=rect(38,418,176,27,'local','white')
        b+=label(48,423,'Uncertainty phrases?','local',11)
        b+=rect(246,203,204,177,'api','api!7!white')
        b+=label(258,215,r'\textbf{Live-data tools}','api',13)
        b+=label(258,239,'Network lookup','muted',10.5)
        for i,t in enumerate(['Open-Meteo · weather','Coinbase · spot quote','BBC · feed entry']):
            b+=rect(260,271+i*28,176,24,'api','white',2)
            b+=label(269,275+i*28,t,'api',10.5)
        b+=label(258,359,'Direct return · no LLM','api',10)
        b+=rect(466,203,204,177,'cloud','cloud!7!white')
        b+=label(478,215,r'\textbf{Cloud inference}','cloud',13)
        b+=label(478,239,'Network request','muted',10.5)
        b+=block(480,271,176,61,'GPT-4o-mini','Cloud adapter\\\\Original request','cloud')
        b+=label(478,350,'Forced mode skips rules','cloud',10.2)
        # A reserved channel below the tools carries fallback into cloud;
        # it does not run through or rewrite a tool response.
        b+=arrow([(214,432),(457,432),(457,301),(480,301)],'cloud',True)
        b+=label(258,442,'Uncertain / local error','cloud',10.5)
        b+=arrow([(126,445),(126,510)],'local')
        b+=label(45,472,'Accept local reply','local',10)
        b+=arrow([(348,380),(348,510)],'api')
        # Mask where the fallback crosses the tool reply, using a small bridge.
        b+='\\draw[white,line width=4pt] (348,428) -- (348,436);\n\\draw[api,line width=.85pt] (348,428) -- (348,436);\n'
        b+=arrow([(568,380),(568,510)],'cloud')
        b+='\\draw[muted,line width=.8pt] (126,510) -- (568,510);\n'
        b+=arrow([(348,510),(348,535)])
        b+=block(215,535,263,64,'Terminal reply + SQLite','Text · source · model · latency\\\\Energy metadata retained with history','ink')
        b+=label(24,620,r'Solid: execution / reply \quad Dashed: conditional cloud fallback',size=10)
        # Right-hand details carry the mechanics omitted from the overview.
        for i,(num,title,sub,col) in enumerate([
            ('1','Live-data keywords','Highest priority','api'),
            ('2','Specialised domains','Then complexity markers','cloud'),
            ('3','More than 150 words','Then local by default','cloud')]):
            y=64+i*78
            b+=rect(732,y,25,25,col,col+'!12!white',12)
            b+=label(740,y+3,num,col,12)
            b+=label(769,y,title,col,12)
            b+=label(769,y+25,sub,'muted',10.2)
        b+=label(732,318,r'\textbf{III. Energy bookkeeping}',size=14)
        b+=label(732,355,'Provider token usage n\\\\+ selected profile c (J/token)',size=11.5)
        b+=arrow([(842,402),(842,426)])
        b+=rect(732,426,230,54,'line','tint!45!white')
        b+=label(746,442,'Wh = n × c / 3,600',size=15)
        b+=label(732,505,'Local: estimate + cloud baseline\\\\Escalated: local + cloud estimates\\\\Tools: no inference estimate',size=10.8)
        b+=label(732,591,'Configured coefficients;\\\\separate from battery telemetry.','muted',10.2)
        return doc(b,w,h)

    def comparison(data,mobile):
        case=data['cases'][0]
        w,h=(350,365) if mobile else (760,310)
        b=label(18,13,'Configured energy at the same 62-token count',size=12 if mobile else 14,width=w-36)
        b+=label(18,65 if mobile else 45,'Estimate (mWh)','muted',10.5)
        x0=68 if mobile else 76
        y0=115 if mobile else 89
        plotw=245 if mobile else 630
        scale=plotw/65
        # Length encodes estimated mWh. Whiskers are the coefficient bounds
        # in the config, not sample standard errors or confidence intervals.
        for j,(col,title,value,bounds) in enumerate([
            ('local','Local profile',case['local_mwh'],case['local_range_mwh']),
            ('cloud','GPT-4o proxy',case['cloud_proxy_mwh'],case['cloud_proxy_range_mwh'])]):
            y=y0+j*88
            b+=label(18,y-31,title,col,11)
            b+=f'\\path[fill={col}!72!white] ({x0},{y}) rectangle ({x0+value*scale:.3f},{y+24});\n'
            low,high=[x0+v*scale for v in bounds]
            b+=f'\\draw[{col},line width=1pt] ({low:.3f},{y+12}) -- ({high:.3f},{y+12});\n'
            for x in [low,high]: b+=f'\\draw[{col},line width=1pt] ({x:.3f},{y+7}) -- ({x:.3f},{y+17});\n'
            b+=label(x0+value*scale+5,y-22,f'{value:.1f}',col,12)
        axis=y0+130
        b+=f'\\draw[muted,line width=.5pt] ({x0},{axis}) -- ({x0+plotw},{axis});\n'
        for tick in [0,20,40,60]:
            x=x0+tick*scale
            b+=f'\\draw[muted,line width=.5pt] ({x},{axis}) -- ({x},{axis+4});\n'
            b+=label(x-4,axis+10,str(tick),'muted',10)
        by=axis+49
        if mobile:
            b+=label(18,by,'0.85 J/token · local coefficient','local',11)
            b+=label(18,by+29,'3.10 J/token · cloud coefficient','cloud',11)
        else:
            b+=label(18,by,'0.85 J/token · local coefficient','local',11)
            b+=label(395,by,'3.10 J/token · cloud coefficient','cloud',11)
        return doc(b,w,h)
    return system,comparison
