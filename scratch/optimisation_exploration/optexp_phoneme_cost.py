"""Keyboard-complexity drop when a phoneme is removed, on the final theory (merged + affix + briefs).

Per spelling (ortho) the outline typed is the most abbreviated one: fewest strokes, then lowest chord cost
(src.keyboard.Starboard.getChordCost summed over the strokes). Complexity = frequency-weighted mean of that cost per word.
Two simulations per phoneme (same removal model as optexp_phoneme_information.py):
  all      the phoneme is removed from every word; collisions are ignored;
  kept     the words that collide after the removal keep their phoneme (their intact outlines), repeated until no collision is left.
           A collision = a typed (shortest) outline of one spelling shared with another spelling that claims it (any outline of the other
           spelling when this is its typed outline, or its typed outline when the claim is any outline of the first).
Affix / brief outlines are fixed strings; the removal is applied to them stroke by stroke where the stroke holds the syllable's old keys.
Writes out/phoneme_cost.tsv. Usage: python scratch/optimisation_exploration/optexp_phoneme_cost.py [--phonemes @,a,...] [--workers 4]
"""
import argparse
import csv
import multiprocessing as mp
import os
import sys
import time
from collections import defaultdict
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import optexp_phoneme_information as pi  # noqa: E402
import src.theorycompare as tc  # noqa: E402
from optexp_common import OUT  # noqa: E402

G = pi.G
Outline = tuple[tuple[int, ...], ...]
BIG = 10 ** 6


def strokeCost(s: tuple[int, ...]) -> int:
    cache: dict[tuple[int, ...], int] = G["strokeCache"]
    c = cache.get(s)
    if c is None:
        r = G["kb"].getChordCost(s)
        c = BIG if r is None else r
        cache[s] = c
    return c


def rank(o: Outline) -> tuple[int, int]:
    return len(o), sum(strokeCost(s) for s in o)


def partialRemap(o: Outline, old: Any, new: Any) -> Outline:
    """Fixed (affix / brief) outline: replace the syllable's old keys by the new ones in each stroke that holds them."""
    strokes = [set(s) for s in o]
    for j in range(min(len(old), len(strokes))):
        if old[j] <= strokes[j]:
            strokes[j] = (strokes[j] - old[j]) | new[j]
    return pi.canon(tuple(tuple(s) for s in strokes))


def prepareCost() -> None:
    pi.prepare()
    G["strokeCache"] = {}
    # same weighting as util.compare_theories: Lexique383 film frequency (summed per lower-cased spelling), over the lexicon spellings
    lexFreq = tc.loadLexicon(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "Lexique383.tsv"), "films").freq
    orthoName = {G["wOrtho"][i]: w.ortho.lower() for i, w in enumerate(G["words"])}
    seen: set[str] = set()
    orthoFreq: dict[int, float] = {}
    for o, name in sorted(orthoName.items()):
        if name in lexFreq and name not in seen:
            seen.add(name)
            orthoFreq[o] = lexFreq[name]
    G["orthoFreq"] = orthoFreq
    orthoWords: dict[int, list[int]] = defaultdict(list)
    for i, o in enumerate(G["wOrtho"]):
        orthoWords[o].append(i)
    fixedOf: dict[int, list[Outline]] = defaultdict(list)
    for name in ("plus_affix", "plus_briefs"):
        for outline, o in G["fixed"][name]:
            fixedOf[o].append(outline)
    merged = G["stageOut"]["merged"]
    outlines: dict[int, list[Outline]] = {}
    for o, ws in orthoWords.items():
        s: dict[Outline, None] = {}
        for i in ws:
            for x in merged[i]:
                s[x] = None
        for x in fixedOf.get(o, ()):
            s[x] = None
        outlines[o] = list(s)
    priced = {o: [x for x in os_ if all(strokeCost(t) < BIG for t in x)] for o, os_ in outlines.items()}
    used = {o: min(os_, key=rank) for o, os_ in priced.items() if os_ and o in G["orthoFreq"]}     # a spelling with no priceable outline is left out (as theorycompare)
    print(f"{len(outlines) - len(used)} spellings without a priceable outline, left out", flush=True)
    claimants: dict[Outline, set[int]] = defaultdict(set)
    for o, os_ in outlines.items():
        for x in os_:
            claimants[x].add(o)
    usedBy: dict[Outline, set[int]] = defaultdict(set)
    for o, u in used.items():
        usedBy[u].add(o)
    freq = G["orthoFreq"]
    G.update(orthoWords=orthoWords, fixedOf=fixedOf, outlines=outlines, used=used, claimants=claimants, usedBy=usedBy,
             totalCost=sum(freq.get(o, 0.0) * rank(u)[1] for o, u in used.items()),
             totalStrokes=sum(freq.get(o, 0.0) * rank(u)[0] for o, u in used.items()),
             totalF=sum(freq.get(o, 0.0) for o in used))
    print(f"{len(used)} spellings; mean cost/word {G['totalCost'] / G['totalF']:.3f}, strokes/word {G['totalStrokes'] / G['totalF']:.3f}", flush=True)


def removedOutlines(o: int, changed: dict[int, Any]) -> list[Outline]:
    s: dict[Outline, None] = {}
    first = None
    for i in G["orthoWords"][o]:
        if i in changed:
            first = first or changed[i]
            old, new = changed[i]
            for x in G["stageOut"]["merged"][i]:
                r = pi.remap(x, old, new)
                if r:
                    s[r] = None
        else:
            for x in G["stageOut"]["merged"][i]:
                s[x] = None
    for x in G["fixedOf"].get(o, ()):
        s[partialRemap(x, *first) if first else x] = None
    return list(s)


def runPhoneme(ph: str) -> dict[str, Any]:
    changed = {i: pi.removed(i, ph) for i in G["byPh"][ph]}
    allAff = {G["wOrtho"][i] for i in changed}
    aff = sorted({G["wOrtho"][i] for i in changed} & G["used"].keys())
    freq, used, claimants, usedBy = G["orthoFreq"], G["used"], G["claimants"], G["usedBy"]
    newOut: dict[int, list[Outline]] = {o: removedOutlines(o, changed) for o in aff}
    newOut = {o: [x for x in xs if all(strokeCost(s) < BIG for s in x)] for o, xs in newOut.items()}
    newUsed: dict[int, Outline | None] = {o: (min(xs, key=rank) if xs else None) for o, xs in newOut.items()}
    affSet = set(aff)

    def totals(rev: set[int]) -> tuple[float, float]:
        dc = ds = 0.0
        for o in aff:
            u = used[o] if o in rev or newUsed[o] is None else newUsed[o]
            assert u is not None
            f = freq.get(o, 0.0)
            dc += f * (rank(used[o])[1] - rank(u)[1])
            ds += f * (rank(used[o])[0] - rank(u)[0])
        return dc, ds

    rev: set[int] = {o for o in aff if newUsed[o] is None}
    allDc, allDs = totals(set(rev))
    rounds = 0
    while True:
        rounds += 1
        cur = {o: (G["outlines"][o] if o in rev else newOut[o]) for o in aff}
        curUsed = {o: (used[o] if o in rev else newUsed[o]) for o in aff}
        local: dict[Outline, set[int]] = defaultdict(set)
        localUsed: dict[Outline, set[int]] = defaultdict(set)
        for o in aff:
            for x in cur[o]:
                local[x].add(o)
            localUsed[curUsed[o]].add(o)     # type: ignore[index]
        add: set[int] = set()
        for o in aff:
            if o in rev:
                continue
            for x in cur[o]:
                others = (claimants.get(x, set()) - affSet) | (local[x] - {o})
                if not others:
                    continue
                usedOthers = (usedBy.get(x, set()) - affSet) | (localUsed.get(x, set()) - {o})
                if curUsed[o] == x or usedOthers:
                    add.add(o)
                    add.update(y for y in local[x] if y != o and y not in rev)
                    break
        if not add:
            break
        rev |= add
    keptDc, keptDs = totals(rev)
    tf = G["totalF"]
    return dict(phoneme=ph, spellings=len(aff), allCost=allDc / tf, allStrokes=allDs / tf, keptCost=keptDc / tf, keptStrokes=keptDs / tf,
                reverted=len(rev), revertedFreq=sum(freq.get(o, 0.0) for o in rev), rounds=rounds)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phonemes", default="")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    prepareCost()
    allPh = sorted((p for p in G["byPh"] if "/" not in p or len(G["byPh"][p]) < len(G["byPh"][p.split("/")[0]])), key=lambda p: -len(G["byPh"][p]))
    todo = args.phonemes.split(",") if args.phonemes else allPh
    t = time.time()
    results = []
    with mp.get_context("fork").Pool(args.workers) as pool:
        for k, r in enumerate(pool.imap(runPhoneme, todo)):
            results.append(r)
            print(f"[{k + 1}/{len(todo)}] {r['phoneme']} {time.time() - t:.0f}s all={r['allCost']:.4f} kept={r['keptCost']:.4f} reverted={r['reverted']}", flush=True)
    cols = ["phoneme", "spellings", "allCost", "allStrokes", "keptCost", "keptStrokes", "reverted", "revertedFreq", "rounds"]
    meta = {"meanCostPerWord": G["totalCost"] / G["totalF"], "meanStrokesPerWord": G["totalStrokes"] / G["totalF"]}
    with open(os.path.join(OUT, "phoneme_cost.tsv"), "w", newline="") as f:
        wr = csv.DictWriter(f, cols, delimiter="\t", extrasaction="ignore")
        wr.writeheader()
        wr.writerows(results)
    with open(os.path.join(OUT, "phoneme_cost_baseline.tsv"), "w") as f:
        f.write("\n".join(f"{k}\t{v}" for k, v in meta.items()) + "\n")


if __name__ == "__main__":
    main()
