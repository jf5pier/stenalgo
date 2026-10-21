"""First-syllable schwa dropped, its onset merged forward: savings, complexity, and the S5 conflicts before / after.

Candidate: a word of >= 2 syllables whose first syllable is exactly onset + schwa (no coda). Compression: that syllable is dropped and its
onset is prepended to the onset of the next one (petit p°ti -> pti, demain d°m5 -> dm5, cela s°la -> sla), so the word has one stroke fewer.
In every outline of the word the first stroke's base keys and the second's are replaced by the merged chord (feature / mark keys of both
strokes are kept, unioned). Legal = every stroke of the compressed outline is a priceable chord (cost < BIG, all phonemes on keys); phoneme
order violations of the merged onset are counted, not forbidden.
Scenarios (typed form = 95% compressed + 5% long, the weights a later CP-SAT run would use; the long form stays typable):
  forced  every legal candidate is compressed, whatever the conflict;
  safe    only the spellings whose compressed outlines are claimed by no other spelling (long or compressed, any dictionary layer),
          fixed point as optexp_reduced_outlines.solve();
  safe+S5 safe, minus the words whose compressed base strokes would join another lemme's S5 cluster (extra row, report only).
Conflicts are the S5 lemma-homophone clusters of src.ambiguitychecker (>= 2 distinct bare lemmes on one base stroke key, before S6/S7).
Read-only on the pipeline outputs. Writes OUT/schwa_merge_{report.md,top100_conflicts.tsv,cp_sat_weights.tsv,sanity_words.tsv,onsets.tsv}
and OUT/reduced_outlines_schwamerge.tsv (affix_abbreviations.tsv format, safe scenario, never a colliding outline).
Run from the repo root, one instance at a time (about 2 GB, 65 s load):
  python scratch/optimisation_exploration/optexp_schwa_merge.py [--limit-candidates N]    (N=0 checks the forced scenario equals the baseline)
"""
import argparse
import csv
import glob
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import optexp_phoneme_cost as pc  # noqa: E402
import optexp_phoneme_information as pi  # noqa: E402
from optexp_common import OUT, canon  # noqa: E402
from plover_stenalgo.plover_stenalgo.stroke import parseOutline  # noqa: E402
from src.ambiguitychecker import (  # noqa: E402
    classifyTheory, computeClusterSizeDistribution, computeOverflowFrequencyMass, loadIgnoredLemmas)
from src.theorycompare import countViolations  # noqa: E402
from util._stenorender import renderFinalStrokesToRTFCRE  # noqa: E402

G = pi.G
Outline = tuple[tuple[int, ...], ...]
SCHWA = "°"
KEEP, SPLIT = 0.05, 0.95            # long-form share, compressed-form share of a compressed word's frequency
SANITY = "petit demain besoin regarde monsieur cela celui ceci depuis venir".split()
C: dict[int, dict[str, Any]] = {}   # word index -> candidate record
ORTHO_NAME: dict[int, str] = {}


# --- candidates -------------------------------------------------------------------------------------------------------------

def compressOutline(s: Outline, old: Any, new0: tuple[int, ...]) -> Outline | None:
    """Replace the base keys of strokes 0 and 1 by the merged chord (the extras of both strokes are kept)."""
    if len(s) < len(old) or len(old) < 2:
        return None
    for j in range(len(old)):
        if not old[j] <= set(s[j]):
            return None
    first = set(new0) | (set(s[0]) - old[0]) | (set(s[1]) - old[1])
    return canon((tuple(first),) + tuple(s[2:]))


def buildCandidates(limit: int | None) -> None:
    kb = G["kb"]
    mismatch = 0
    firstNuclei: Counter[str] = Counter()
    for i, parts in enumerate(G["wParts"]):
        if len(parts) < 2:
            continue
        first = parts[0]
        if first.get("coda") or not first.get("onset"):
            continue
        firstNuclei["".join(first.get("nucleus", []))] += 1
        if first.get("nucleus") != [SCHWA]:
            continue
        if len(G["wBase"][i]) != len(parts):
            mismatch += 1
            continue
        if limit is not None and len(C) >= limit:
            break
        second = parts[1]
        merged = {part: list(ph) for part, ph in second.items()}
        merged["onset"] = list(first["onset"]) + list(second.get("onset", []))
        try:
            stroke0: tuple[int, ...] | None = tuple(sorted(set(kb.getStrokeOfSyllableByPart(merged))))
        except (IndexError, KeyError):
            stroke0 = None
        legal = bool(stroke0) and pc.strokeCost(stroke0) < pc.BIG        # type: ignore[arg-type]
        try:
            groups: list[tuple[int, ...]] | None = [tuple(kb.getStrokesOfPhoneme(p, "onset")[0]) for p in merged["onset"]]
            viol: int | None = countViolations(groups)
        except IndexError:
            viol = None
        outlines: list[Outline] = []
        base: Outline | None = None
        if legal:
            assert stroke0 is not None
            for o in G["stageOut"]["merged"][i]:
                r = compressOutline(o, G["wBase"][i], stroke0)
                if r and all(pc.strokeCost(t) < pc.BIG for t in r) and r not in outlines:
                    outlines.append(r)
            base = canon((stroke0,) + tuple(tuple(sorted(x)) for x in G["wBase"][i][2:]))
        C[i] = dict(onset="".join(merged["onset"]), firstOnset="".join(first["onset"]), stroke0=stroke0, legal=legal,
                    usable=bool(outlines), outlines=outlines, base=base, violations=viol, mergedParts=merged)
    print(f"{len(C)} candidate words ({sum(1 for c in C.values() if c['legal'])} legal chord, {sum(1 for c in C.values() if c['usable'])} usable); "
          f"{mismatch} skipped (syllable/stroke count mismatch); first-syllable onset+nucleus histogram: {firstNuclei.most_common(6)}", flush=True)
    assert limit is not None or len(C) > 1000, "unexpectedly few candidates: is the schwa phoneme spelled differently?"


def compressedOutlinesBySpelling() -> dict[int, list[Outline]]:
    out: dict[int, dict[Outline, None]] = defaultdict(dict)
    for i, c in C.items():
        if c["usable"]:
            for x in c["outlines"]:
                out[G["wOrtho"][i]][x] = None
    return {o: list(xs) for o, xs in out.items()}


# --- scenarios --------------------------------------------------------------------------------------------------------------

def solveSafe(comp: dict[int, list[Outline]]) -> tuple[set[int], dict[int, list[str]]]:
    """(spellings that stay compressed, for each reverted spelling the other spellings it collided with)."""
    claimants: dict[Outline, set[int]] = G["claimants"]
    rev: dict[int, list[str]] = {}
    while True:
        local: dict[Outline, set[int]] = defaultdict(set)
        for o, xs in comp.items():
            if o not in rev:
                for x in xs:
                    local[x].add(o)
        add: dict[int, list[str]] = {}
        for o, xs in comp.items():
            if o in rev:
                continue
            for x in xs:
                others = (claimants.get(x, set()) - {o}) | (local[x] - {o})
                if others:
                    add.setdefault(o, []).extend(sorted(ORTHO_NAME.get(y, "?") for y in others)[:3])
                    for y in local[x] - {o}:
                        add.setdefault(y, []).append(ORTHO_NAME[o])
        if not add:
            break
        rev.update(add)
    return {o for o in comp if o not in rev}, rev


def wordsOfSpellings(spellings: set[int]) -> set[int]:
    return {i for i, c in C.items() if c["usable"] and G["wOrtho"][i] in spellings}


def theoryOf(compressed: set[int]) -> dict[Any, list[Any]]:
    theory: dict[Any, list[Any]] = defaultdict(list)
    for i, w in enumerate(G["words"]):
        theory[C[i]["base"] if i in compressed else canon(G["wBase"][i])].append(w)
    return theory


def clusterStats(theory: dict[Any, list[Any]]) -> tuple[dict[str, Any], dict[Any, Any]]:
    reports = classifyTheory(theory, ignoredLemmas=frozenset(G["ignored"]))
    dist = computeClusterSizeDistribution(reports)
    overflowMass, mass, overflowKeys = computeOverflowFrequencyMass(reports)
    lh = {k: r for k, r in reports.items() if r.lemmaHomophoneAmbiguous}
    return dict(clusters=len(lh), mass=mass, overflowClusters=len(overflowKeys), overflowMass=overflowMass,
                sizeCounts=dict(sorted(dist.lemmaHomophoneCountCounts.items())),
                sizeFreq=dict(sorted(dist.lemmaHomophoneCountFrequency.items())),
                sameLemmaClusters=sum(1 for r in reports.values() if r.sameLemmaAmbiguous)), lh


def classify(before: dict[Any, Any], after: dict[Any, Any], compWords: set[Any]) -> dict[str, Any]:
    """new = no pre-existing conflict among the uncompressed words of the cluster; enlarged = pre-existing and a compressed word joined."""
    new: list[Any] = []
    enlarged: list[Any] = []
    unchanged = 0
    for k, r in after.items():
        if not any(w in compWords for w in r.words):
            unchanged += 1
        elif len({w.lemme for w in r.words if w not in compWords}) >= 2:
            enlarged.append(k)
        else:
            new.append(k)
    dissolved = sum(1 for k in before if k not in after)
    return dict(new=new, enlarged=enlarged, unchanged=unchanged, dissolved=dissolved,
                newMass=sum(after[k].totalFrequency for k in new), enlargedMass=sum(after[k].totalFrequency for k in enlarged))


def price(spellings: set[int], best: dict[int, Outline], used: dict[int, Outline]) -> dict[str, Any]:
    """Gain of the compressed outlines against `used` (the shipped short form, or the dictionary-only long form)."""
    freq = G["orthoFreq"]
    n = 0
    f = ds = dc = 0.0
    for o in spellings:
        if o not in used or o not in best:
            continue
        u, b = used[o], best[o]
        if pc.rank(b) >= pc.rank(u):
            continue
        n += 1
        f += freq.get(o, 0.0)
        ds += freq.get(o, 0.0) * (len(u) - len(b))
        dc += freq.get(o, 0.0) * (pc.rank(u)[1] - pc.rank(b)[1])
    tf = G["totalF"]
    return dict(spellings=n, freqShare=f / tf, strokes100=ds / tf, cost100=dc / tf, strokes9505=SPLIT * ds / tf, cost9505=SPLIT * dc / tf)


def s5Clean(spellings: set[int], before: dict[Any, Any]) -> set[int]:
    """Drop (monotone fixed point) the spellings with a compressed word in a new / enlarged S5 cluster."""
    cur = set(spellings)
    while True:
        words = wordsOfSpellings(cur)
        wordObjs = {G["words"][i] for i in words}
        _, lh = clusterStats(theoryOf(words))
        bad: set[int] = set()
        for k, r in lh.items():
            if any(w in wordObjs for w in r.words):
                for i in words:
                    if G["words"][i] in r.words:
                        bad.add(G["wOrtho"][i])
        if not bad:
            return cur
        cur -= bad


# --- weights ----------------------------------------------------------------------------------------------------------------

def weightsOf(compressed: set[int]) -> Counter[tuple[str, str]]:
    cnt: Counter[tuple[str, str]] = Counter()

    def add(syls: list[dict[str, list[str]]], w: float) -> None:
        for syl in syls:
            if syl.get("onset"):
                cnt[("onset-cluster", "".join(syl["onset"]))] += w
            for part, phs in syl.items():
                for ph in phs:
                    cnt[(f"phoneme-{part}", ph)] += w
    for i, parts in enumerate(G["wParts"]):
        f = G["wFreq"][i]
        if i in compressed:
            add([C[i]["mergedParts"]] + parts[2:], SPLIT * f)
            add(parts, KEEP * f)
        else:
            add(parts, f)
    return cnt


# --- output helpers ---------------------------------------------------------------------------------------------------------

def md(header: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def text(kb: Any, o: Outline) -> str:
    return str(renderFinalStrokesToRTFCRE(kb, o))


def f4(x: float) -> str:
    return f"{x:.4f}"


def loadShipped() -> dict[str, set[str]]:
    shipped: dict[str, set[str]] = defaultdict(set)
    for path in sorted(glob.glob("plover_stenalgo_*.json")):
        with open(path, encoding="utf8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            for t, word in data.items():
                if isinstance(word, str):
                    shipped[t].add(word)
    return shipped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-candidates", type=int, default=None, help="keep the first N candidates only (0 = the zero-candidate baseline check)")
    args = ap.parse_args()
    t0 = time.time()
    pc.prepareCost()
    G["ignored"] = loadIgnoredLemmas()
    kb, freq, used, tf = G["kb"], G["orthoFreq"], G["used"], G["totalF"]
    for i, w in enumerate(G["words"]):
        ORTHO_NAME[G["wOrtho"][i]] = w.ortho
    buildCandidates(args.limit_candidates)
    comp = compressedOutlinesBySpelling()
    best: dict[int, Outline] = {o: min(xs, key=pc.rank) for o, xs in comp.items()}
    baseCost, baseStrokes = G["totalCost"] / tf, G["totalStrokes"] / tf
    # reference 2: the dictionary alone (no affix, no brief outline), the "long form" of compare_theories
    longRef: dict[int, Outline] = {}
    for o, ws in G["orthoWords"].items():
        outs = [x for i in ws for x in G["stageOut"]["merged"][i] if all(pc.strokeCost(t) < pc.BIG for t in x)]
        if outs and o in used:
            longRef[o] = min(outs, key=pc.rank)
    baseCostD = sum(freq.get(o, 0.0) * pc.rank(u)[1] for o, u in longRef.items()) / tf
    baseStrokesD = sum(freq.get(o, 0.0) * pc.rank(u)[0] for o, u in longRef.items()) / tf

    # baseline and scenarios
    beforeStats, beforeLH = clusterStats(theoryOf(set()))
    zeroStats, _ = clusterStats(theoryOf(set()))
    assert zeroStats == beforeStats
    forcedSp = set(comp)
    safeSp, reverted = solveSafe(comp)
    cleanSp = s5Clean(safeSp, beforeLH)
    scen: dict[str, dict[str, Any]] = {}
    for name, sp in (("forced", forcedSp), ("safe", safeSp), ("safe+S5", cleanSp)):
        words = wordsOfSpellings(sp)
        wobj = {G["words"][i] for i in words}
        st, lh = clusterStats(theoryOf(words))
        scen[name] = dict(spellings=sp, words=words, wobj=wobj, stats=st, lh=lh, cls=classify(beforeLH, lh, wobj), price=price(sp, best, used), priceDict=price(sp, best, longRef))
    print(f"[{time.time() - t0:.0f}s] scenarios done: " + ", ".join(f"{n}: {len(s['spellings'])} spellings" for n, s in scen.items()), flush=True)
    if args.limit_candidates == 0:
        assert scen["forced"]["stats"] == beforeStats, "forced with zero candidates differs from the baseline"
        print("zero-candidate check: forced scenario equals the baseline")
    emptyCheck = clusterStats(theoryOf(set()))[0] == beforeStats

    # the safe rows, round trip and clashes
    shipped = loadShipped()
    rows: list[tuple[str, Outline, Outline, int]] = []        # spelling, long (typed), compressed, ortho
    for o in sorted(safeSp):
        if o not in used:
            continue
        if o not in longRef:
            continue
        for x in comp[o]:
            if pc.rank(x) < pc.rank(longRef[o]):
                rows.append((ORTHO_NAME[o], longRef[o], x, o))
    texts: dict[str, set[str]] = defaultdict(set)
    bad = 0
    for name, _, b, _o in rows:
        tx = text(kb, b)
        parsed = parseOutline(tuple(tx.split("/")))
        if parsed is None or canon(parsed) != canon(b):
            bad += 1
        texts[tx].add(name)
    clash = [(t, ws | shipped[t]) for t, ws in texts.items() if len(ws | shipped[t]) > 1]
    print(f"safe rows {len(rows)}; round-trip failures: {bad}; outlines claimed by several spellings (shipped dictionaries included): {len(clash)}")
    for t, ws in clash[:10]:
        print("  ", t, sorted(ws))
    tsv = os.path.join(OUT, "reduced_outlines_schwamerge.tsv")
    written = 0
    with open(tsv, "w", encoding="utf8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t")
        wr.writerow(["spelling", "long", "short", "saved", "rank", "anchor", "k", "frequency", "route"])
        for name, u, b, _o in rows:
            tx = text(kb, b)
            if len(texts[tx] | shipped[tx]) > 1:
                continue
            wr.writerow([name, text(kb, u), tx, len(u) - len(b), 1, name, 1, 0, "schwamerge"])
            written += 1
    print(f"wrote {tsv} ({written} rows)")
    boundary = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "optexp_reduced_boundary.py"), tsv],
                              capture_output=True, text=True).stdout.strip()

    # onset inventory (complexity)
    inv: dict[str, dict[str, Any]] = {}
    for i, c in C.items():
        d = inv.setdefault(c["onset"], dict(words=0, freq=0.0, legal=c["legal"], violations=c["violations"], usable=0))
        d["words"] += 1
        d["freq"] += G["wFreq"][i]
        d["usable"] += int(c["usable"])
    with open(os.path.join(OUT, "schwa_merge_onsets.tsv"), "w", encoding="utf8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t")
        wr.writerow(["onset", "words", "usableWords", "frequency", "legal", "orderViolations"])
        for k, d in sorted(inv.items(), key=lambda kv: -kv[1]["freq"]):
            wr.writerow([k, d["words"], d["usable"], f"{d['freq']:.2f}", d["legal"], d["violations"]])
    keysLong = keysComp = ws_ = 0.0
    for name, u, b, o in rows:
        w_ = freq.get(o, 0.0)
        keysLong += w_ * sum(len(s) for s in u) / len(u)
        keysComp += w_ * sum(len(s) for s in b) / len(b)
        ws_ += w_

    # forced top 100
    forced = scen["forced"]
    fcls = forced["cls"]
    comps = forced["wobj"]
    top: list[tuple[float, Any]] = sorted(((forced["lh"][k].totalFrequency, k) for k in fcls["new"] + fcls["enlarged"]), key=lambda t: -t[0])[:100]
    nameOf = {G["words"][i]: i for i in range(len(G["words"]))}
    with open(os.path.join(OUT, "schwa_merge_top100_conflicts.tsv"), "w", encoding="utf8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t")
        wr.writerow(["rank", "outline", "kind", "lemmes", "summedFrequency", "words(ortho[lemme/gramCat/freq])", "compressed", "preexisting",
                     "winner", "winnerFrequency", "lostStrokesPerWord", "lostCostPerWord", "lostFrequency"])
        for rk, (tot, k) in enumerate(top, 1):
            r = forced["lh"][k]
            ws = sorted(r.words, key=lambda w: (-w.frequency, w.ortho))
            cw = [w for w in ws if w in comps]
            pre = [w for w in ws if w not in comps]
            winner = ws[0]
            lost = {G["wOrtho"][nameOf[w]] for w in cw if w is not winner}
            ls = lc = lf = 0.0
            for o in lost:
                if o in longRef and o in best and pc.rank(best[o]) < pc.rank(longRef[o]):
                    ls += freq.get(o, 0.0) * (len(longRef[o]) - len(best[o]))
                    lc += freq.get(o, 0.0) * (pc.rank(longRef[o])[1] - pc.rank(best[o])[1])
                    lf += freq.get(o, 0.0)
            try:
                tx = text(kb, k)
            except Exception:
                tx = str(k)
            wr.writerow([rk, tx, "new" if k in set(fcls["new"]) else "enlarged", r.lemmaHomophoneLemmaCount, f"{tot:.2f}",
                         "; ".join(f"{w.ortho}[{w.lemme}/{w.gramCat.name if hasattr(w.gramCat, 'name') else w.gramCat}/{w.frequency:.1f}]" for w in ws),
                         ",".join(w.ortho for w in cw), ",".join(w.ortho for w in pre), winner.ortho, f"{winner.frequency:.2f}",
                         f"{ls / tf:.6f}", f"{lc / tf:.6f}", f"{lf:.1f}"])

    # CP-SAT weights
    wb, ws2, wf = weightsOf(set()), weightsOf(scen["safe"]["words"]), weightsOf(scen["forced"]["words"])
    with open(os.path.join(OUT, "schwa_merge_cp_sat_weights.tsv"), "w", encoding="utf8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t")
        wr.writerow(["kind", "item", "baseline", "safe_95_5", "forced_95_5"])
        for key in sorted(set(wb) | set(ws2) | set(wf), key=lambda k: (k[0], -wf.get(k, 0.0))):
            wr.writerow([key[0], key[1], f"{wb.get(key, 0.0):.2f}", f"{ws2.get(key, 0.0):.2f}", f"{wf.get(key, 0.0):.2f}"])

    # sanity words
    claimants = G["claimants"]
    sanity: list[list[Any]] = []
    for name in SANITY:
        for i, w in enumerate(G["words"]):
            if w.ortho != name:
                continue
            o = G["wOrtho"][i]
            c = C.get(i)
            comp_ = best.get(o) if c and c["usable"] else None
            longTyped = used.get(o)
            others = sorted({x.lemme for x in forced["lh"].get(c["base"], type("E", (), {"words": []})).words if x.lemme != w.lemme}) if c and c["base"] else []
            claim = sorted(ORTHO_NAME.get(y, "?") for y in claimants.get(comp_, set()) - {o}) if comp_ else []
            sanity.append([name, w.lemme, getattr(w.gramCat, "name", w.gramCat), "".join(t for t in w.phonology) if not isinstance(w.phonology, str) else w.phonology,
                           "yes" if c else "no", c["onset"] if c else "", "yes" if c and c["legal"] else "no",
                           text(kb, canon(G["wBase"][i])), text(kb, longTyped) if longTyped else "",
                           text(kb, comp_) if comp_ else "", len(longTyped) if longTyped else "", len(comp_) if comp_ else "",
                           ",".join(claim), ",".join(others), "yes" if o in safeSp and c else "no"])
    sanHeader = ["word", "lemme", "gramCat", "phonology", "candidate", "mergedOnset", "legal", "longBase", "longTyped", "compressed", "strokesLong",
                 "strokesComp", "finalClaimants", "S5Conflicts(forced)", "safe"]
    with open(os.path.join(OUT, "schwa_merge_sanity_words.tsv"), "w", encoding="utf8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t")
        wr.writerow(sanHeader)
        wr.writerows(sanity)

    # report
    def clusterRow(label: str, st: dict[str, Any], cl: dict[str, Any] | None) -> list[Any]:
        return [label, st["clusters"], f"{st['mass']:.0f}", st["overflowClusters"], f"{st['overflowMass']:.0f}",
                "" if cl is None else f"{len(cl['new'])} / {cl['newMass']:.0f}", "" if cl is None else f"{len(cl['enlarged'])} / {cl['enlargedMass']:.0f}",
                "" if cl is None else cl["dissolved"]]
    candFreq = sum(G["wFreq"][i] for i in C)
    topCand = sorted((o for o in comp if o in freq), key=lambda o: -freq[o])[:25]
    safeSet = safeSp
    L: list[str] = []
    L.append("# First-syllable schwa merge (study)\n")
    L.append(f"Generated by optexp_schwa_merge.py ({time.time() - t0:.0f} s). Typed cost = {SPLIT} x compressed + {KEEP} x long. "
             f"Film frequencies (Lexique383) for the savings, Word.frequency for the S5 clusters.\n")
    L.append(f"Candidates: {len(C)} words, {sum(1 for c in C.values() if c['legal'])} with a legal merged chord, {sum(1 for c in C.values() if c['usable'])} usable, "
             f"{len(comp)} spellings, {100 * candFreq / sum(G['wFreq']):.2f}% of the summed word frequency. "
             f"Baseline: {baseStrokes:.4f} strokes/word, chord cost {baseCost:.4f}/word.\n")
    L.append("## 1. Savings (per word, frequency weighted)\n")
    hdr = ["scenario", "spellings that gain", "freq share", "strokes saved 100%", "cost saved 100%", "strokes saved 95/5", "cost saved 95/5"]
    L.append(f"Against the shipped short form (dictionary + affix + briefs; {baseStrokes:.4f} strokes, {baseCost:.3f} cost per word):\n")
    L.append(md(hdr, [[n, s["price"]["spellings"], f"{100 * s['price']['freqShare']:.2f}%", f4(s["price"]["strokes100"]), f4(s["price"]["cost100"]),
                  f4(s["price"]["strokes9505"]), f4(s["price"]["cost9505"])] for n, s in scen.items()]))
    L.append(f"\nAgainst the dictionary alone, the long form ({baseStrokesD:.4f} strokes, {baseCostD:.3f} cost per word):\n")
    L.append(md(hdr, [[n, s["priceDict"]["spellings"], f"{100 * s['priceDict']['freqShare']:.2f}%", f4(s["priceDict"]["strokes100"]), f4(s["priceDict"]["cost100"]),
                  f4(s["priceDict"]["strokes9505"]), f4(s["priceDict"]["cost9505"])] for n, s in scen.items()]))
    L.append(f"\nSafe: {len(safeSp)} of {len(comp)} candidate spellings stay compressed, {len(reverted)} are reverted by a collision "
             f"(the TSV carries {written} outlines, each shorter than the dictionary outline; compare_theories prices it against the short form).\n")
    L.append("## 2. Complexity\n")
    L.append(f"Distinct merged onsets: {len(inv)} ({sum(1 for d in inv.values() if d['legal'])} legal, {sum(1 for d in inv.values() if not d['legal'])} illegal). "
             f"Mean keys per stroke of the safe rows (frequency weighted): long {keysLong / max(ws_, 1e-9):.3f}, compressed {keysComp / max(ws_, 1e-9):.3f}.\n")
    L.append(md(["merged onset", "words", "usable", "frequency", "legal", "order violations"],
                [[k, d["words"], d["usable"], f"{d['freq']:.0f}", d["legal"], d["violations"]] for k, d in sorted(inv.items(), key=lambda kv: -kv[1]["freq"])[:30]]))
    L.append("\nBoundary risk of the safe rows (optexp_reduced_boundary.py):\n\n```\n" + boundary + "\n```\n")
    L.append("Most frequent candidate spellings and their fate:\n")
    rows2 = []
    for o in topCand:
        fate = "safe" if o in safeSp else ("reverted: " + ", ".join(dict.fromkeys(reverted.get(o, [])[:3]))) if o in reverted else "?"
        rows2.append([ORTHO_NAME[o], f"{freq[o]:.0f}", text(kb, longRef[o]) if o in longRef else "", text(kb, used[o]) if o in used else "", text(kb, best[o]), fate])
    L.append(md(["spelling", "film freq", "dictionary", "short form now", "compressed", "fate"], rows2))
    L.append("\nExceptions: the most frequent reverted spellings above are the rule's exceptions (function words listed first); "
             f"{len(reverted)} reverted spellings in all, {sum(1 for c in C.values() if not c['legal'])} words with an illegal merged chord.\n")
    L.append("## 3-4. S5 lemma-homophone clusters (before S6/S7)\n")
    L.append("Clusters = distinct bare lemmes >= 2 on one base stroke key; mass = summed Word.frequency; overflow = >= 5 lemmes. "
             "new = no conflict among the uncompressed words, enlarged = a compressed word joins an existing conflict, dissolved = before-clusters that no longer exist.\n")
    rowsC = [clusterRow("before (long forms)", beforeStats, None)] + [clusterRow(n, s["stats"], s["cls"]) for n, s in scen.items()]
    L.append(md(["scenario", "clusters", "mass", "overflow clusters", "overflow mass", "new (n / mass)", "enlarged (n / mass)", "dissolved"], rowsC))
    L.append("\nCluster size distribution (lemmes -> clusters):\n")
    sizes = sorted(set(beforeStats["sizeCounts"]) | {k for s in scen.values() for k in s["stats"]["sizeCounts"]})
    L.append(md(["lemmes"] + ["before"] + list(scen), [[n, beforeStats["sizeCounts"].get(n, 0)] + [s["stats"]["sizeCounts"].get(n, 0) for s in scen.values()] for n in sizes]))
    L.append(f"\nSafe+S5 keeps {len(cleanSp)} of {len(safeSp)} safe spellings. Zero-candidate check (scenario function with no word compressed equals the baseline): {emptyCheck}.\n")
    L.append("Note: the safe scenario is conflict-free on the final outlines (marks and features included); its S5 clusters are the conflicts before S6/S7 would separate them.\n")
    L.append("## Sanity words\n")
    L.append(md(sanHeader, sanity))
    L.append(f"\nVerification: safe round-trip failures {bad}, clashes against the shipped dictionaries and among the rows {len(clash)}.\n")
    with open(os.path.join(OUT, "schwa_merge_report.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(L))
    print(f"[{time.time() - t0:.0f}s] report written")
    for n, s in scen.items():
        print(n, "short:", s["price"], "dict:", s["priceDict"], s["stats"]["clusters"], f"{s['stats']['mass']:.0f}", {k: (len(v) if isinstance(v, list) else v) for k, v in s["cls"].items()})
    print("before", beforeStats["clusters"], f"{beforeStats['mass']:.0f}", beforeStats["overflowClusters"])


if __name__ == "__main__":
    main()
