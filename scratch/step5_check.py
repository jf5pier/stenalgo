"""Step 5 check (plan 2026-10-01): with a copy of the decisions minus the `tion` and `ner` fusions and minus the `i` growth,
the proposals must reproduce the D numbers of scratch/fusion-check-2026-10-01.md (+344, +1,578) and `i:[mn][aeiouy]` as the best growth.
Run: PYTHONUNBUFFERED=1 PYTHONPATH=. env/bin/python scratch/step5_check.py"""
import json, time
from src import affixes as A, affixproposals as P
from src.affixbinding import PhonemeKeys, enumerateKeypresses
from src.affixdecisions import Decisions, saveDecisions, loadDecisions
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory

TION = ("suffix", "ccion|cion|cyon|sion|ssion|tion|tions", "sj§")
NER = ("suffix", "ner|nez|nner|nnée|née|nées", "ne")
I = ("prefix", "e|hi|hy|i|y|î", "i")
d = loadDecisions()
entries = [e for e in d.entries.values() if e.key not in (TION, NER)]
tmp = Decisions(entries)
import dataclasses
tmp = tmp.withEntry(dataclasses.replace(d.entries[I], growth=None))
saveDecisions(tmp, "scratch/step5-decisions.json")
t = time.time()
sb = Starboard.fromJSONFile("starboard3h.json")
phonetic, disambiguated, _w, _l = loadPhoneticAndDisambiguatedTheory(sb)
records, _ = A.extractRecords(phonetic, disambiguated)
pool = A.buildCandidates(records, A.loadSeeds()[0], decisions=tmp)
ctx = A.SimContext(sb, records); pk = PhonemeKeys(sb); keypresses = enumerateKeypresses(sb, ctx)
print(f"loaded {time.time() - t:.0f}s", flush=True)
byKey = {(c.position, c.ortho, c.phono): c for c in pool.values() if c.k == 1}
rules = json.load(open("affix_rules.json"))
keysOf = {(r["position"], r["ortho"], r["phono"]): tuple(r["keys"]) for r in rules}
selected = frozenset(keysOf)
for key, expected in ((TION, 344), (NER, 1578)):
    t = time.time()
    p = P.proposeFusion(byKey[key], pool, tmp, pk, ctx, keypresses, selected, print)
    print(f"FUSION {key[1][:30]}: net {p.net:+.0f} (D md: {expected:+d}); {p.line()} [{time.time() - t:.0f}s]", flush=True)
t = time.time()
g = P.proposeGrowth(byKey[I], tmp, keysOf[I], ctx)
print(f"GROWTH `i`: best {g.label!r} net {g.net:+.0f}; {g.line()}; alternatives {g.alternatives} [{time.time() - t:.0f}s]", flush=True)
