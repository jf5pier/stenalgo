import sys, time
sys.argv = sys.argv[:1]
src = open("scratch/re_fusion.py").read().split('K2, K17')[0]
exec(src)
forms = groups["re+ré (merged)"]
two = [k for k in kps if len(k) == 2]
print(len(kps), "legal keypresses,", len(two), "with 2 keys", flush=True)
t = time.time(); rows = []
for k in two:
    r = evalKey(forms, k); rows.append((r["score"], k, r))
rows.sort(key=lambda x: -x[0])
print(f"{time.time()-t:.0f}s")
for sc, k, r in rows[:12]:
    print(f"{k} score {sc:7.0f} benefit {r['benefit']:6.0f} hits {r['hits']} hard exc {r['exc']} (freq {r['excFreq']:.0f}) {r['top'][:4]}")
