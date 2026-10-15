"""How many collisions does each phoneme prevent, at each stage of the theory?

Read-only on the pipeline outputs (PhoneticTheory.pickle, Dictionary.pickle, DisambiguatedTheory.pickle, the Plover JSONs).
For each phoneme the removal is simulated per word (the phoneme is dropped from each syllable, the syllable's keys are rebuilt
by the keyboard, and in every later outline the old base keys are replaced by the new ones; feature, mark and merge keys stay).
Stages: S5 phonetic | S6 base+feature (no marks) | S7 +marks (long outlines) | merged (final pickle, all outlines)
        | +affix dictionary | +brief dictionary.
A collision = one canonical outline shared by two different spellings (as src.ambiguitychecker.findFinalCollisions).
Usage: python scratch/optimisation_exploration/optexp_phoneme_information.py [--phonemes @,a,...] [--workers 4]
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
from optexp_common import MARKS, OUT, canon, loadAll, loadPlover  # noqa: E402
from plover_stenalgo.plover_stenalgo.stroke import parseOutline  # noqa: E402
from src.mergedfeaturekeys import splitLongAlternates  # noqa: E402

STAGES = ["S5_phonetic", "S6_feature", "S7_marks", "merged", "plus_affix", "plus_briefs"]
G: dict[str, Any] = {}      # shared (fork) state


def strip(o: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return canon(tuple(tuple(k for k in s if k not in MARKS) for s in o))


def prepare() -> None:
    t = time.time()
    kb, dictionary, dis, base = loadAll()
    words = [w for w in dis if w in base]
    print(f"{len(words)} words in both theories ({len(dis) - len(words)} only in the disambiguated one)", flush=True)
    orthoId: dict[str, int] = {}
    wOrtho, wFreq, wLemma, wParts, wBase = [], [], [], [], []
    stageOut: dict[str, list[list[Any]]] = {s: [] for s in STAGES[:4]}
    badSplit = 0
    for w in words:
        o = orthoId.setdefault(w.ortho, len(orthoId))
        wOrtho.append(o); wFreq.append(w.frequency); wLemma.append(w.lemme)
        wParts.append([dictionary.syllableCollection.syllable_names[n].phonemeNamesByPart()
                       for n in w.phonemesToSyllableNames(withSilent=False)])
        wBase.append(tuple(frozenset(s) for s in base[w]))
        outs = [canon(x) for x in dis[w]]
        res = None
        for aligned in range(1, len(outs) + 1):
            res = splitLongAlternates(outs, aligned)
            if res is not None:
                break
        assert res is not None
        s7: list[Any] = []
        for i in range(aligned):
            s7.extend(res[i] if res[i] else [outs[i]])
        stageOut["S5_phonetic"].append([canon(base[w])])
        stageOut["S7_marks"].append(s7)
        stageOut["S6_feature"].append(list(dict.fromkeys(strip(x) for x in s7)))
        stageOut["merged"].append(list(dict.fromkeys(outs)))
    fixed: dict[str, list[tuple[Any, int]]] = {}
    freqOfOrtho: dict[str, float] = defaultdict(float)
    for w in words:
        freqOfOrtho[w.ortho] = max(freqOfOrtho[w.ortho], w.frequency)
    for name, path in (("plus_affix", "plover_stenalgo_affix_dictionary.json"), ("plus_briefs", "plover_stenalgo_brief_dictionary.json")):
        entries = []
        for text, ortho in loadPlover(path).items():
            parsed = parseOutline(tuple(text.split("/")))
            if parsed is None:
                continue
            entries.append((canon(parsed), orthoId.setdefault(ortho, len(orthoId))))
        fixed[name] = entries
    G.update(words=words, wOrtho=wOrtho, wFreq=wFreq, wLemma=wLemma, wParts=wParts, wBase=wBase, stageOut=stageOut, fixed=fixed,
             kb=kb, orthoFreq={orthoId[o]: f for o, f in freqOfOrtho.items()}, totalFreq=sum(wFreq))
    # phoneme -> word indices
    byPh: dict[str, list[int]] = defaultdict(list)
    for i, parts in enumerate(wParts):
        for ph in {p for syl in parts for part in syl.values() for p in part}:
            byPh[ph].append(i)
        for part in ("onset", "coda"):
            for ph in {p for syl in parts for p in syl[part]}:
                byPh[f"{ph}/{part}"].append(i)
    G["byPh"] = byPh
    print(f"prepared in {time.time() - t:.0f}s; S7 split anomalies: {badSplit}", flush=True)


def removed(i: int, ph: str) -> tuple[tuple[frozenset[int], ...], tuple[tuple[int, ...], ...]]:
    """(old base strokes, new base strokes) of word i without phoneme ph."""
    kb = G["kb"]
    ph, _, only = ph.partition("/")          # "l" = every part, "l/onset" or "l/coda" = that part only
    new = []
    for syl in G["wParts"][i]:
        parts = {part: [p for p in phs if p != ph or (only and part != only)] for part, phs in syl.items()}
        new.append(frozenset(kb.getStrokeOfSyllableByPart(parts)))
    return G["wBase"][i], tuple(new)


def remap(o: tuple[tuple[int, ...], ...], old: Any, new: Any) -> tuple[tuple[int, ...], ...] | None:
    strokes = [set(s) for s in o]
    for j in range(len(old)):
        if j >= len(strokes) or not old[j] <= strokes[j]:
            return None
        strokes[j] = (strokes[j] - old[j]) | new[j]
    return canon(tuple(tuple(s) for s in strokes))


def collisions(claims: Any) -> dict[str, float]:
    """claims: iterable of (outline, orthoId, freq, lemma). Colliding groups / words / excess frequency."""
    groups: dict[Any, dict[int, float]] = {}
    lemmas: dict[Any, set[str]] = {}
    for outline, o, f, lemma in claims:
        g = groups.get(outline)
        if g is None:
            groups[outline] = {o: f}
            lemmas[outline] = {lemma}
        else:
            g[o] = max(g.get(o, 0.0), f) if o in g else f
            lemmas[outline].add(lemma)
    n = words = cross = same = 0
    excess = 0.0
    for outline, g in groups.items():
        if len(g) < 2:
            continue
        n += 1
        words += len(g)
        excess += sum(g.values()) - max(g.values())
        if len(lemmas[outline]) > 1:
            cross += 1
        else:
            same += 1
    return {"groups": n, "words": words, "excessFreq": excess, "crossLemmaGroups": cross, "sameLemmaGroups": same}


def stageClaims(stage: str, ph: str | None) -> tuple[list[Any], int]:
    """All claims of a stage, with phoneme `ph` removed (None = intact). Second value: words left without an outline."""
    changed: dict[int, Any] = {}
    emptied = 0
    if ph is not None:
        for i in G["byPh"].get(ph.split("/")[0] if "/" not in ph else ph, []):
            changed[i] = removed(i, ph)
    claims = []
    base = "merged" if stage in ("plus_affix", "plus_briefs") else stage
    for i, outs in enumerate(G["stageOut"][base]):
        if i in changed:
            old, new = changed[i]
            outs2 = []
            for o in outs:
                r = remap(o, old, new)
                if r:
                    outs2.append(r)
            if not outs2:
                emptied += 1
            outs = list(dict.fromkeys(outs2))
        f, o_, lem = G["wFreq"][i], G["wOrtho"][i], G["wLemma"][i]
        for outline in outs:
            claims.append((outline, o_, f, lem))
    if stage in ("plus_affix", "plus_briefs"):
        for name in STAGES[4:STAGES.index(stage) + 1]:
            for outline, o_ in G["fixed"][name]:
                claims.append((outline, o_, G["orthoFreq"].get(o_, 0.0), "\0fixed" + str(o_)))
    return claims, emptied


def runPhoneme(ph: str | None) -> list[dict[str, Any]]:
    rows = []
    for stage in STAGES:
        claims, emptied = stageClaims(stage, ph)
        r = collisions(claims)
        r.update(phoneme=ph or "(intact)", stage=stage, wordsEmptied=emptied, claims=len(claims))
        rows.append(r)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phonemes", default="")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    prepare()
    # a part variant is only worth running when the phoneme also occurs in another part (else it equals "both")
    allPh = sorted((p for p in G["byPh"] if "/" not in p or len(G["byPh"][p]) < len(G["byPh"][p.split("/")[0]])),
                   key=lambda p: -len(G["byPh"][p]))
    todo: list[str | None] = [None] + (args.phonemes.split(",") if args.phonemes else allPh)
    print("phonemes:", allPh, flush=True)
    t = time.time()
    with mp.get_context("fork").Pool(args.workers) as pool:
        results = []
        for k, rows in enumerate(pool.imap(runPhoneme, todo)):
            results.extend(rows)
            print(f"[{k + 1}/{len(todo)}] {todo[k]} {time.time() - t:.0f}s", flush=True)
    os.makedirs(OUT, exist_ok=True)
    cols = ["phoneme", "stage", "groups", "words", "excessFreq", "crossLemmaGroups", "sameLemmaGroups", "wordsEmptied", "claims"]
    with open(os.path.join(OUT, "phoneme_information_raw.tsv"), "w", newline="") as f:
        wr = csv.DictWriter(f, cols, delimiter="\t", extrasaction="ignore")
        wr.writeheader()
        wr.writerows(results)
    print("raw written", flush=True)


if __name__ == "__main__":
    main()
