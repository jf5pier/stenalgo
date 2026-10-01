import json
from util import affix_scan as S
from src.affixes import SimContext
starboard = S.loadStarboard(); records = S.loadRecords(starboard, False)
ctx = SimContext(starboard, records)
m = json.load(open("starboard3h.json"))["phonemesAssignedToStroke"]
by = {}
for r in records: by.setdefault(r.ortho, r)
A = {18, 22}
def words(base): return sorted({x.ortho for x in ctx.baseIndex.get(base, ())})[:6]
print("fallback stroke (18,22) alone is an existing single-stroke outline?", (18, 22) in ctx.singleStrokeOutlines, "-> words:", words(((18, 22),)))
for w in ("entraîne", "enchaîne", "enseigne", "entracte", "enferme", "enflamme"):
    r = by[w]; stem = r.base[1]
    union = tuple(sorted(set(stem) | A))
    nb = (union,) + tuple(r.base[2:])
    print(f"{w:10} stem stroke {stem} + rule keys {sorted(A)} -> chord {union}; legal? {ctx.isLegal(union)}; "
          f"overlap {sorted(set(stem) & A)}; other words with that new outline: {words(nb)}; words with the bare stem outline {r.base[1:]}: {words(tuple(r.base[1:]))}")
print("words whose phonology is /tREnk/ or contains it:", sorted({r.ortho for r in records if 'tREnk' in ''.join(r.phonoSylls)})[:10])
print("words spelled with stem stroke tREn (same first stroke as entraîne):", sorted({r.ortho for r in records if r.base and r.base[0] == by['entraîne'].base[1]})[:10])
