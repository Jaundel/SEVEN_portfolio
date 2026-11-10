"""Reproduce SEVEN explanatory figures from tracked source coefficients.
Run: python tools/build_figures.py
Requires matplotlib. No model inference or external data requests are used.
"""
from pathlib import Path
import json, csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/figures'
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads((ROOT / 'data/energy_profiles.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','axes.labelcolor':'#222222','text.color':'#222222','axes.edgecolor':'#555555','savefig.facecolor':'white'})
BLUE='#2166ac'; ORANGE='#b35806'; GREEN='#287d66'; GRAY='#59636e'

def save(fig, name):
    fig.savefig(OUT / (name+'.svg'), bbox_inches='tight',metadata={'Date':None})
    fig.savefig(OUT / (name+'.png'), bbox_inches='tight',dpi=160)
    plt.close(fig)

def box(ax,x,y,w,h,text,color='#eef1f4',size=11):
    ax.add_patch(Rectangle((x,y),w,h,facecolor=color,edgecolor='#68727d',lw=1))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=size,linespacing=1.35)

def arrow(ax, a,b, text='', color=GRAY, dashed=False, offset=(0,0)):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=12,color=color,lw=1.2,linestyle='--' if dashed else '-'))
    if text: ax.text((a[0]+b[0])/2+offset[0],(a[1]+b[1])/2+offset[1],text,ha='center',va='center',fontsize=9,color=color,bbox={'facecolor':'white','edgecolor':'none','pad':2})

# Explanatory architecture, manually specified from router.py and api_check.py.
f,ax=plt.subplots(figsize=(11,7.3));ax.set(xlim=(0,11),ylim=(0,7.2));ax.axis('off')
box(ax,3.8,6.55,3.4,.5,'User prompt')
box(ax,3.8,5.35,3.4,.75,'Ordered rule checks\nkeywords · domain\ncomplexity · length',size=9.5)
arrow(ax,(5.5,6.55),(5.5,6.1))
box(ax,.15,3.8,2.7,.7,'API context\n+ local synthesis','#edf4fa')
box(ax,4.05,3.8,2.9,.7,'Local inference\nLemonade Server','#edf7f1')
box(ax,8.05,3.8,2.8,.7,'Cloud inference\nconfigured provider','#fff4e9')
arrow(ax,(4.2,5.35),(1.5,4.5),'API_CHECK',BLUE,offset=(-.15,.08))
arrow(ax,(5.5,5.35),(5.5,4.5),'LOCAL',GREEN,offset=(.38,0))
arrow(ax,(6.8,5.35),(9.4,4.5),'CLOUD',ORANGE,offset=(.1,.08))
box(ax,3.8,2.1,3.4,.8,'Response validation\nempty / explicit uncertainty?')
arrow(ax,(1.5,3.8),(3.8,2.7), 'API result*',BLUE,offset=(-.2,.07))
arrow(ax,(5.5,3.8),(5.5,2.9))
arrow(ax,(7.2,2.65),(9.4,3.8),'retry if enabled',ORANGE,True,offset=(.2,-.05))
box(ax,3.8,.55,3.4,.75,'Response\n+ estimated energy')
arrow(ax,(5.5,2.1),(5.5,1.3),'return',GREEN,offset=(.4,0))
ax.plot([9.45,9.45,7.2],[3.8,.92,.92],color=ORANGE,lw=1.2)
arrow(ax,(7.8,.92),(7.2,.92),color=ORANGE)
ax.text(.15,.17,'* API context can be returned directly if local synthesis fails. Local errors also trigger cloud fallback.\nForced-cloud mode bypasses the classifier. Cloud failures may return the prior local answer or raise an error.',fontsize=9,va='top',color=GRAY)
save(f,'routing-architecture')

f,ax=plt.subplots(figsize=(9.5,5.5))
for key,color,style in [('local',BLUE,'-'),('cloud',ORANGE,'--')]:
 p=DATA[key]; n=list(range(1,1001)); y=[i*p['joules_per_token']/3600 for i in n]
 lo=[i*p['coefficient_min']/3600 for i in n]; hi=[i*p['coefficient_max']/3600 for i in n]
 ax.fill_between(n,lo,hi,color=color,alpha=.10,linewidth=0)
 ax.plot(n,y,color=color,lw=2,ls=style,label=p['plot_label'])
ax.set(xlabel='Token count supplied to the estimator',ylabel='Estimated energy (Wh)',xlim=(0,1000),ylim=(0,1.02))
ax.grid(axis='y',color='#e1e4e8',lw=.7);ax.set_axisbelow(True);ax.legend(loc='upper left',frameon=False)
ax.text(0,-.23,'Shading: configured coefficient bounds, not a confidence interval.\nThese curves evaluate the software profiles, not measured device power.',transform=ax.transAxes,fontsize=9,color=GRAY)
f.subplots_adjust(bottom=.23);save(f,'energy-estimate')
with (ROOT/'data/energy_estimates.csv').open('w') as out:
 w=csv.writer(out);w.writerow(['tokens','local_estimate_Wh','cloud_estimate_Wh'])
 for n in [100,250,500,750,1000]:
  w.writerow([n,format(n*DATA['local']['joules_per_token']/3600,'.9f'),format(n*DATA['cloud']['joules_per_token']/3600,'.9f')])
