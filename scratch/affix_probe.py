import pickle, sys, collections
from src import affixes as A, affixbinding as B
from util.affix_scan import loadStarboard, loadRecords
sb=loadStarboard(); recs=loadRecords(sb,False)
fams=pickle.load(open("scratch/affix-families.pickle","rb"))
ctx=A.SimContext(sb,recs)
import json
d=json.load(open("scratch/affix_bindings.json"))
byid={f.familyId:f for f in fams}
for b in d["bound"]:
    if b["family_id"] not in sys.argv[1:]: continue
    f=byid[b["family_id"]]
    groups=[]
    for s in b["subgroups"]:
        mem=[i for i,m in enumerate(f.members) if m.ortho in s["members"]]
        groups.append((A.Binding(f.position,A.MERGED,tuple(s["keys"])),[c for c in f.carriers if c.member in mem]))
    res=A.simulate(groups,ctx)
    print(f.familyId,[m.ortho+"/"+m.phono for m in f.members])
    mc=collections.Counter(r.markCost for rs in res for r in rs if r.gain>0)
    print(" benefiting markCost dist",dict(mc))
    # partner collisions: benefiting carriers whose newBase equals another word's outline
    n=0;ex=[]
    for rs in res:
        for r in rs:
            if r.gain>0 and r.markCost>0:
                n+=1
                if len(ex)<8: ex.append((r.carrier.rec.ortho,[o.ortho for o in ctx.baseIndex.get(r.newBase,[]) if o.ortho!=r.carrier.rec.ortho][:3]))
    print(" marked",n,ex)
