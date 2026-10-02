import sys,re
sys.path.insert(0,'.')
from src.verbparadigm import isWellFormedSplice
bad=[];e=f=0
for r in open('/tmp/o.tsv').read().split('\n')[1:]:
    x=r.split('\t')
    if len(x)<9: continue
    if not isWellFormedSplice(x[1],x[8]): bad.append((x[0],x[1],x[2],x[8],x[12]))
    u=re.split(r'[|_]',x[8])
    if '' in u:e+=1
    if any(len(k)>1 and k.endswith('#') for k in u):f+=1
print(len(bad),e,f)
for b in bad:print(b)
