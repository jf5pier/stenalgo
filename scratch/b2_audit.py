"""Classify B2 backtest mismatches: attested-row consistency vs generator gap.

For every phon/syll mismatch, capture the context of the differing nucleus:
syllable position (word-final or not, closed or open), the orthographic unit
there, the infinitive's attested breakdown, and how the lemma's other attested
forms spell the same orthographic unit (internal-consistency vote).
"""
import sys, csv, collections, difflib
sys.path.insert(0, ".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH

theory, _ = loadTheoryAndKeyboard()
vt = vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex = vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct = vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables = vp.deriveConjugationEndingTables(theory, vt, ex)
inf = vp.attestedInfinitiveWordByLemme(theory)

# Attested Mixte rows by (lemme): ortho -> (tag, phon, syll_cv, orthosyll_cv)
mixte = collections.defaultdict(list)
for r in csv.DictReader(open("resources/LexiqueMixte.tsv"), delimiter="\t"):
    if r["cgram"] == "VER":
        mixte[r["lemme"]].append(r)

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
        # nucleus-level diff of the phoneme strings
        gu, _ = vp._unitsAndBoundaries(g.rawSyllCV)
        au, ab = vp._unitsAndBoundaries(r["syll_cv"])
        if len(gu) != len(au):
            rows.append((r["lemme"], r["ortho"], tag, g.phonology, r["phon"], "UNIT-COUNT", "", ""))
            continue
        nuclei = [i for i, u in enumerate(au) if vp._hasNucleus(u)]
        lastNucleus = nuclei[-1] if nuclei else -1
        coda = [u for u in au[lastNucleus + 1:] if u != "#"] if nuclei else []
        for i, (a, b) in enumerate(zip(gu, au)):
            if a != b:
                final = i == lastNucleus
                closed = bool(coda) if final else any(not vp._hasNucleus(u) for u in au[i + 1:nuclei[nuclei.index(i) + 1]]) if i in nuclei else False
                ctx = ("final-closed" if closed else "final-open") if final else ("mid-closed" if closed else "mid-open")
                # ortho unit at that position, when aligned
                ou, _ = vp._unitsAndBoundaries(g.rawOrthosyllCV)
                ounit = ou[i] if len(ou) == len(au) else "?"
                rows.append((r["lemme"], r["ortho"], tag, a, b, ctx, ounit, iw.rawSyllCV))
                break

print(f"{len(rows)} phonology mismatches")
cnt = collections.Counter((a, b, ctx, ounit) for _, _, _, a, b, ctx, ounit, _ in rows)
for k, n in cnt.most_common(40):
    exs = [r for r in rows if (r[3], r[4], r[5], r[6]) == k][:3]
    print(f"{n:5d}  {k[0]!r}->{k[1]!r}  {k[2]:<13} ortho={k[3]!r:<5} e.g. "
          + ", ".join(f"{e[1]}/{e[2]}" for e in exs))
