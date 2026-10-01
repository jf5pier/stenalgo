"""One-off migration (2026-10-01, plan step 1): src/affixscopes tables + the pool's merged anchors -> affix_decisions.json.
Run: PYTHONPATH=. env/bin/python scratch/migrate_affix_decisions.py
Reads the legacy copy scratch/affixscopes_legacy.py (the live module is replaced by src/affixdecisions.py)."""
import sys, json, pickle
sys.path.insert(0, "scratch")
import affixscopes_legacy as L
from src import affixes as A

NOTES = {
    "scope": "growth scope decided 2026-09-30 (scratch/scope-decisions-2026-09-30.md)",
    "none": "no growth, decided 2026-09-30 (scratch/scope-decisions-2026-09-30.md)",
    "fusionApproved": "fusion approved 2026-10-01 (scratch/fusion-check-2026-10-01.md)",
    "grandfathered": "merged anchor that is itself one of the 30 selected rules: kept fused (grandfathered, never judged as a fusion)",
    "refused": "fusion not approved 2026-10-01 (scratch/fusion-check-2026-10-01.md): parts stay apart",
}
NUMBERS = {  # fused - alone deltas of scratch/fusion-check-2026-10-01.md for the approved fusions
    ("prefix", "am|an|ant|em|en|ench|enh|ham|han|hen", "@"): {"fusedMinusAlone": 1340},
    ("suffix", "ner|nez|nner|nnée|née|nées", "ne"): {"fusedMinusAlone": 1578},
    ("suffix", "der|dé|dée", "de"): {"fusedMinusAlone": 494},
    ("suffix", "ccion|cion|cyon|sion|ssion|tion|tions", "sj§"): {"fusedMinusAlone": 344},
}

def formJson(f):
    return {"label": f.label, "anchors": sorted(f.anchors) if f.anchors is not None else None,
            "sound": f.sound.pattern if f.sound else None, "spelling": f.spelling.pattern if f.spelling else None}

def entry(key, verdict, forms, note, date, numbers=None):
    pos, ortho, phono = key
    return {"position": pos, "spellings": ortho, "phono": phono, "verdict": verdict,
            "growth": [formJson(f) for f in forms], "refused": [], "note": note, "date": date, "numbers": numbers or {}}

out = []
for key, forms in L.SCOPES.items():
    merged = "|" in key[1]
    note = NOTES["grandfathered"] if merged else NOTES["scope" if forms else "none"]
    if merged and forms:
        note = NOTES["scope"] + "; " + NOTES["grandfathered"]
    out.append(entry(key, "fused" if merged else "-", forms, note, "2026-09-30"))
for key, forms in L.APPROVED_FUSIONS.items():
    out.append(entry(key, "fused", forms, NOTES["fusionApproved"], "2026-10-01", NUMBERS.get(key)))
have = {(e["position"], e["spellings"], e["phono"]) for e in out}
assert len(have) == len(out)

records, _ = A.extractRecords(*__import__("util._theoryio", fromlist=["x"]).loadPhoneticAndDisambiguatedTheory(
    __import__("src.keyboard", fromlist=["x"]).Starboard.fromJSONFile("starboard3h.json"))[:2])
seedPairs, _ = A.loadSeeds()
pool = A.buildCandidates(records, seedPairs)
nApart = 0
for c in sorted(pool.values(), key=lambda c: (c.position, c.phono, c.ortho)):
    if not (c.isAnchor and c.mergeParts):
        continue
    merged = (c.position, c.ortho, c.phono)
    parts = [(p[0], p[3], p[2]) for p in c.mergeParts]
    v = L.fusionVerdict(merged, parts)
    if v == "apart" and merged not in have:
        out.append(entry(merged, "apart", [], NOTES["refused"], "2026-10-01"))
        have.add(merged)
        nApart += 1
print(len(L.SCOPES), "scopes,", len(L.APPROVED_FUSIONS), "approved fusions,", nApart, "explicit apart")
json.dump({"format": 1, "anchors": out}, open("affix_decisions.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
