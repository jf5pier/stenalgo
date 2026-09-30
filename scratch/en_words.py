import json
from util import affix_scan as S
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
m = json.load(open("starboard3h.json"))["phonemesAssignedToStroke"]
part = {k: p for p, ks in json.load(open("starboard3h.json"))["keyIDinSyllabicPart"].items() for k in ks}
by = {}
for r in records: by.setdefault(r.ortho, r)
def show(stroke): return f"{tuple(stroke)}={m.get(str(tuple(stroke)), '?')}"
for w in ("entraîne", "enchaîne", "enseigne", "entracte", "enferme", "enflamme", "endorme", "enzyme", "entame"):
    r = by.get(w)
    if r is None: print(w, "not found"); continue
    print(f"{w:10} phono {'.'.join(r.phonoSylls):14} strokes {[tuple(s) for s in r.base]}  stem first stroke keys {sorted(r.base[1])} -> " + ", ".join(f"{k}:{part[k][0]}" for k in sorted(r.base[1])))
# what phoneme is on each coda key
print({k: m.get(f"({k},)") for k in range(16, 26)})
print({k: v for k, v in m.items() if any(p in v for p in ("N", "J", "k", "n", "m"))})
