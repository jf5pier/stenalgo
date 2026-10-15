"""Examples of the collisions created by one fusion exchange: python optexp_fusion_examples.py PHONEME PART SRC DST (SRC typed with DST's keys)."""
import os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optexp_phoneme_information as m
import optexp_phoneme_fusion as fu
G = m.G
src, part, dst = sys.argv[2], sys.argv[1], sys.argv[3]   # part src dst
m.prepare()
changed = [i for i, p in enumerate(G["wParts"]) if any(src in s[part] for s in p)]
cs = set(changed); index = defaultdict(list)
for i, outs in enumerate(G["stageOut"]["merged"]):
    for o in outs: index[o].append(("w", i))
for name in ("plus_affix", "plus_briefs"):
    for o, ortho in G["fixed"][name]: index[o].append(("f", ortho))
names = {v: k for k, v in {w.ortho: i for i, w in enumerate(G["words"])}.items()}
fresh = defaultdict(set)
for i in changed:
    old, new = fu.substituted(i, part, src, dst)
    for o in G["stageOut"]["merged"][i]:
        r = m.remap(o, old, new)
        if r: fresh[r].add(i)
out = []
for o, ws in fresh.items():
    others = {(k, i) for k, i in index.get(o, []) if not (k == "w" and i in cs)}
    names_o = {G["words"][i].ortho for i in ws} | {G["words"][i].ortho if k == "w" else None for k, i in others if k == "w"}
    if len(names_o - {None}) > 1:
        out.append((max(G["wFreq"][i] for i in ws), o, sorted(G["words"][i].ortho for i in ws)[:3],
                    sorted({G["words"][i].ortho for k, i in others if k == "w"})[:3], [i for k, i in others if k == "f"][:1]))
for t in sorted(out, reverse=True)[:12]: print(t)
