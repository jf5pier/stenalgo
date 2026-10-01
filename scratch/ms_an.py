import subprocess,json,hashlib,os,collections,sys
sys.path.insert(0,'.')
from src.verbparadigm import isWellFormedSplice
old=subprocess.run(['git','show','HEAD:resources/LexiqueSynthetic.tsv'],capture_output=True,text=True).stdout.split('\n')
new=open('resources/LexiqueSynthetic.tsv').read().split('\n')
so,sn=set(old),set(new)
add=sn-so;rem=so-sn
print('rows added',len(add),'removed',len(rem))
lem=lambda r:r.split('\t')[2] if r.count('\t')>2 else '?'
for nm,s in(('added',add),('removed',rem)):
    print(nm,collections.Counter(lem(r) for r in s).most_common(25))
bad=empty=fused=0;ex=[]
for r in new[1:]:
    f=r.split('\t')
    if len(f)<9: continue
    ph,sy=f[1],f[8]
    if not isWellFormedSplice(ph,sy): bad+=1;ex.append(r[:80])
    u=sy.split('|')
    if any(x=='' for x in u): empty+=1
    if any(len(x)>1 and x.endswith('#') for x in sy.replace('|','_').split('_') if False) or any(len(x)>1 and x.endswith('#') for x in u): fused+=1
print('guardfail',bad,'empty',empty,'fused',fused,ex[:5])
B='scratch/ms-before/'
files=['phonetic_theory.tsv','disambiguated_theory.tsv','resolved_press_sets.json','keypress_groups.json','realization_report.json','plover_stenalgo_dictionary.json']
md=lambda p:hashlib.md5(open(p,'rb').read()).hexdigest()
for f in files: print(f,'identical' if md(B+f)==md(f) else 'CHANGED')
for f in sorted(os.listdir(B+'data')):
    p='steno-trainer/public/data/'+f
    print('data/'+f,'identical' if md(B+'data/'+f)==md(p) else 'CHANGED')
a=json.load(open(B+'plover_stenalgo_dictionary.json'));b=json.load(open('plover_stenalgo_dictionary.json'))
print('entries',len(a),len(b))
va,vb=set(a.values()),set(b.values())
lost=va-vb;gain=vb-va
print('lost',len(lost),'gained',len(gain))
dl={lem(r) for r in rem}
ow=lambda r:r.split('\t')[0]
rw={ow(r) for r in rem}
print('lost in removed rows',len(lost&rw))
if len(lost)<60:print(sorted(lost))
else:print(sorted(lost)[:60])
if len(gain)<60:print(sorted(gain))
else:print(sorted(gain)[:60])
print('lost not in removed rows',sorted(lost-rw)[:40])
