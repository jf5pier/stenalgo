"""Enumerate every backtest row whose only diff is a plain-e nucleus, and classify it."""
import sys, csv, collections
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)

def plainEPositions(g):
    """(index, context) of plain-'e' ortho nuclei where generated is coarse e."""
    units, boundaries = vp._unitsAndBoundaries(g.rawSyllCV)
    ortho, _ = vp._unitsAndBoundaries(g.rawOrthosyllCV)
    if len(units) != len(ortho): return []
    nuclei = [i for i, u in enumerate(units) if vp._hasNucleus(u)]
    out = []
    for pos, n in enumerate(nuclei):
        if ortho[n] != "e" or units[n] != "e": continue
        if pos == len(nuclei) - 1 or not any(b > n for b in boundaries):
            out.append((n, "final")); continue
        first = not any(b <= n for b in boundaries)
        nxt = next((u for u in ortho[n+1:] if u != "#"), None)
        dbl = nxt if (nxt and len(nxt) == 2 and nxt[0] == nxt[1] and nxt[0].isalpha() and nxt[0] not in "aeiouy") else (nxt if nxt == "sc" else None)
        syllEnd = min(b for b in boundaries if b > n)
        closed = any(u != "#" and not vp._hasNucleus(u) for u in units[n+1:syllEnd])
        out.append((n, ("first+" if first else "") + ("dbl:" + dbl if dbl else ("closed" if closed else "open"))))
    return out

rows = []
for r in csv.DictReader(open("resources/LexiqueMixte.tsv"), delimiter="\t"):
    if r["cgram"] != "VER": continue
    tags = [t for t in r["infover"].split(";") if t]
    if "inf" in tags: continue
    tn = vp.getTrustedTemplate(r["lemme"], vt, ex); iw = inf.get(r["lemme"])
    if tn is None or iw is None or tn not in ct: continue
    for tag in tags:
        p = tag.split(":")
        if len(p) != 3: continue
        g = vp.generateMissingConjugatedForm(r["lemme"], ct[tn], iw, f"{p[0]}:{p[1]}", p[2], tables, minMatchRate=1.0)
        if g is None or g.ortho != r["ortho"] or g.phonology == r["phon"]: continue
        # single-letter e->E diff at a plain-e position
        diffs = [(i, a, b) for i, (a, b) in enumerate(zip(g.phonology, r["phon"])) if a != b]
        if not (len(diffs) == 1 and diffs[0][1] == "e" and diffs[0][2] == "E"): continue
        poss = [c for _, c in plainEPositions(g)]
        rows.append((r["ortho"], tag, poss))

cls = collections.Counter()
byclass = collections.defaultdict(set)
for ortho, tag, poss in rows:
    c = "+".join(sorted(set(poss))) if poss else "?"
    cls[c] += 1; byclass[c].add(ortho)
print(f"{len(rows)} plain-e e->E mismatch rows")
for c, n in cls.most_common():
    print(f"{n:4d}  {c:24} e.g. {sorted(byclass[c])[:8]}")
