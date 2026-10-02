import re, sys
sys.path.insert(0, ".")
exec(open("scratch/en_phon_scope.py").read().split("rows = [")[0])
m = pat(f"[{C}]*@")
cs = [sc.two(c) if sc.neigh[c.rec.idx] in m else c for c in sc.ones]
res = sc._run(cs)
failed = {r.carrier.rec.idx for r in res if r.carrier.span == 2 and r.gain <= 0}
cs = [sc.byIdx[c.rec.idx] if c.rec.idx in failed else c for c in cs]
res = sc._run(cs)
gain = sorted((r for r in res if r.carrier.span == 2 and r.gain > 0), key=lambda r: -r.carrier.rec.frequency)
print(len(gain), "words really gain a 2-stroke form")
for r in gain[:14]:
    rec = r.carrier.rec
    print(rec.ortho, "|", "-".join(rec.phonoSylls[:3]), "| gain", round(r.gain, 1))
