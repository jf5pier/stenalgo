"""The cheap route: shorter outlines for a SET of removed phonemes, as an extra abbreviation file (no layout change, no rebuild).

For the phoneme variants given (e.g. Z/onset,d/onset) every spelling that has them is typed without them wherever that causes no
collision (same fixed-point model as optexp_phoneme_cost.py, applied to the set at once). The reduced outlines that are cheaper than the
spelling's current typed outline are written to OUT/reduced_outlines.tsv in the affix_abbreviations.tsv format, so that
  python -m util.compare_theories ... --stenalgo-abbreviations affix_abbreviations.tsv --stenalgo-abbreviations briefs.tsv
         --stenalgo-abbreviations scratch/optimisation_exploration/out/reduced_outlines.tsv
prices the real effect (the same metric as P18). The script also checks the written outlines against the shipped dictionaries.
Usage: python scratch/optimisation_exploration/optexp_reduced_outlines.py --phonemes Z/onset,d/onset [--tag NAME]
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import optexp_phoneme_cost as pc  # noqa: E402
import optexp_phoneme_information as pi  # noqa: E402
from optexp_common import OUT  # noqa: E402
from plover_stenalgo.plover_stenalgo.stroke import parseOutline  # noqa: E402
from util._stenorender import renderFinalStrokesToRTFCRE  # noqa: E402

G = pi.G
Outline = tuple[tuple[int, ...], ...]


def removedSet(i: int, phs: str) -> tuple[Any, Any]:
    """Like pi.removed, for several phoneme variants at once ('Z/onset,d/onset')."""
    kb = G["kb"]
    variants = [v.partition("/")[::2] for v in phs.split(",")]       # (phoneme, only-part or "")
    new = []
    for syl in G["wParts"][i]:
        parts = {part: [p for p in phonemes if not any(p == ph and (not only or part == only) for ph, only in variants)]
                 for part, phonemes in syl.items()}
        new.append(frozenset(kb.getStrokeOfSyllableByPart(parts)))
    return G["wBase"][i], tuple(new)


def solve(phs: str) -> tuple[list[int], set[int], dict[int, list[Outline]]]:
    """(affected spellings, spellings that must keep their phoneme, reduced outlines of each affected spelling)."""
    words: set[int] = set()
    for v in phs.split(","):
        words.update(G["byPh"][v])
    changed = {i: removedSet(i, phs) for i in words}
    aff = sorted({G["wOrtho"][i] for i in changed} & G["used"].keys())
    freq, used, claimants, usedBy = G["orthoFreq"], G["used"], G["claimants"], G["usedBy"]
    newOut: dict[int, list[Outline]] = {o: pc.removedOutlines(o, changed) for o in aff}
    newOut = {o: [x for x in xs if all(pc.strokeCost(s) < pc.BIG for s in x)] for o, xs in newOut.items()}
    newUsed: dict[int, Outline | None] = {o: (min(xs, key=pc.rank) if xs else None) for o, xs in newOut.items()}
    affSet = set(aff)
    rev: set[int] = {o for o in aff if newUsed[o] is None}
    while True:
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
    return aff, rev, newOut


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phonemes", required=True, help="a set 'Z/onset,d/onset'; several sets separated by ';' (the theory loads once)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--long", action="store_true",
                    help="LONG-form model: the dictionary alone (no affix or brief outline as claimant or typed form); writes a "
                         "dictionary JSON (base + reduced outlines) for util.compare_theories --stenalgo-dict")
    args = ap.parse_args()
    if args.long:
        original = pi.prepare

        def prepareDictionaryOnly() -> None:
            original()
            G["fixed"] = {"plus_affix": [], "plus_briefs": []}
        pi.prepare = prepareDictionaryOnly
    G["long"] = args.long
    pc.prepareCost()
    for one in args.phonemes.split(";"):
        print(f"=== {one}", flush=True)
        runSet(argparse.Namespace(phonemes=one, tag=args.tag if ";" not in args.phonemes else ""))


def runSet(args: argparse.Namespace) -> None:
    for v in args.phonemes.split(","):
        assert v in G["byPh"], f"unknown phoneme variant {v}"
    aff, rev, newOut = solve(args.phonemes)
    used, freq, kb = G["used"], G["orthoFreq"], G["kb"]
    orthoName = {G["wOrtho"][i]: w.ortho for i, w in enumerate(G["words"])}
    # the reduced outline of a spelling: its cheapest merged-stage remap, written only if it beats the current typed outline
    rows = []
    for o in aff:
        if o in rev or not newOut[o]:
            continue
        best = min(newOut[o], key=pc.rank)
        if pc.rank(best) >= pc.rank(used[o]):
            continue
        rows.append((orthoName[o], used[o], best, o))
    gain = sum(freq.get(o, 0.0) * (pc.rank(u)[1] - pc.rank(b)[1]) for _, u, b, o in rows) / G["totalF"]
    print(f"{len(aff)} spellings with the phonemes, {len(rev)} keep them, {len(rows)} get a cheaper outline; "
          f"estimated drop {gain:.3f} per word ({100 * gain / (G['totalCost'] / G['totalF']):.2f}% of the {G['totalCost'] / G['totalF']:.2f} baseline)")

    # C1, learnability: per variant, the share (by film frequency, and by spelling count) of the spellings carrying it that are reduced
    reduced = {o for _, _, _, o in rows}
    print("rule coverage per variant (reduced share by frequency / by spelling count, exceptions = spellings that keep it):")
    for v in args.phonemes.split(","):
        os_ = {G["wOrtho"][i] for i in G["byPh"][v]} & G["used"].keys()
        fAll = sum(freq.get(o, 0.0) for o in os_)
        fRed = sum(freq.get(o, 0.0) for o in os_ if o in reduced)
        print(f"  {v}: {len(os_)} spellings, reduced {100 * fRed / max(fAll, 1e-12):.1f}% by frequency, "
              f"{100 * len(os_ & reduced) / max(len(os_), 1):.1f}% by count, {len(os_ - reduced)} exceptions")
        top = sorted(os_ - reduced, key=lambda o: -freq.get(o, 0.0))[:8]
        print("     most frequent exceptions:", ", ".join(orthoName[o] for o in top))

    # independent check against the shipped dictionaries and among the new outlines
    shipped: dict[str, set[str]] = defaultdict(set)
    shippedFiles = ("plover_stenalgo_dictionary.json",) if G["long"] else (
        "plover_stenalgo_dictionary.json", "plover_stenalgo_affix_dictionary.json", "plover_stenalgo_brief_dictionary.json")
    for path in shippedFiles:
        with open(path, encoding="utf8") as f:
            for text, word in json.load(f).items():
                shipped[text].add(word)
    texts: dict[str, set[str]] = defaultdict(set)
    bad = 0
    for name, _, b, _o in rows:
        text = renderFinalStrokesToRTFCRE(kb, b)
        parsed = parseOutline(tuple(text.split("/")))
        if parsed is None or pi.canon(parsed) != pi.canon(b):
            bad += 1
        texts[text].add(name)
    clash = [(t, ws | shipped[t]) for t, ws in texts.items() if len(ws | shipped[t]) > 1]
    print(f"round-trip failures: {bad}; outlines claimed by several spellings (including the shipped dictionaries): {len(clash)}")
    for t, ws in clash[:10]:
        print("  ", t, sorted(ws))

    tag = args.tag or args.phonemes.replace("/", "").replace(",", "_")
    if G["long"]:
        with open("plover_stenalgo_dictionary.json", encoding="utf8") as f:
            dictionary: dict[str, str] = json.load(f)
        added = 0
        for name, _, b, _o in rows:
            text = renderFinalStrokesToRTFCRE(kb, b)
            if len(texts[text] | shipped[text]) > 1 or text in dictionary:
                continue                    # never add a colliding outline
            dictionary[text] = name
            added += 1
        path = os.path.join(OUT, f"dictionary_long_{tag}.json")
        with open(path, "w", encoding="utf8") as f:
            json.dump(dictionary, f, ensure_ascii=False, indent=1, sort_keys=True)
        print(f"wrote {path} ({added} reduced outlines added)")
        return
    path = os.path.join(OUT, f"reduced_outlines_{tag}.tsv")
    with open(path, "w", encoding="utf8", newline="") as f:
        wr = csv.writer(f, delimiter="\t")
        wr.writerow(["spelling", "long", "short", "saved", "rank", "anchor", "k", "frequency", "route"])
        for name, u, b, _o in rows:
            text = renderFinalStrokesToRTFCRE(kb, b)
            if len(texts[text] | shipped[text]) > 1:
                continue                    # never write a colliding outline
            wr.writerow([name, renderFinalStrokesToRTFCRE(kb, u), text, len(u) - len(b), 1, name, 1, 0, "reduced"])
    print("wrote", path)


if __name__ == "__main__":
    main()
