import pickle, sys
import src.affixes as A
pool = pickle.load(open("scratch/affix-pool.pickle", "rb"))
old = pickle.load(open("scratch/old-a7-nodes.pickle", "rb"))
for name in sys.argv[1:]:
    ok = [k for k in old if k[0]=="suffix" and k[3]==name]
    for k in ok:
        f, ids = old[k]
        print("OLD", k, f, len(ids))
    ids = old[ok[0]][1]
    fq = {c.rec.idx: c.rec.frequency for v in pool.values() for c in v.carriers}
    tot = sum(fq.get(i,0) for i in ids)
    rows=[]
    for k2,v in pool.items():
        if k2[0]!="suffix": continue
        s={c.rec.idx for c in v.carriers}
        inter=ids&s
        if inter: rows.append((sum(fq.get(i,0) for i in inter)/tot, k2, len(s), v.isAnchor, v.exceptionCount))
    rows.sort(reverse=True)
    for r in rows[:6]: print("  ", f"{r[0]:.2f}", r[1][1], r[1][2], r[1][3], "n=",r[2],"anchor",r[3],"exc",r[4])
    # words of old not covered by anything at k>=2
    print("  words in old node:", len(ids), "with any pool carrier:", sum(1 for i in ids if i in fq))
