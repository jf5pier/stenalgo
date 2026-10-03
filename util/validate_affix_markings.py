"""
Diagnostic (hand-run, read-only): check that the affix abbreviations carry the conjugation / homograph markings
of the regular theory, route by route, and explain every route that has no abbreviation.

Run: python -m util.validate_affix_markings [--examples N]   (about 40 s; N: print N examples of each kind of lost route; needs the same inputs as util.export_affix_dictionary)
Exit code 0: no violation; 1: a violation (listed).

Checks, on the abbreviations rebuilt exactly as `util.export_affix_dictionary` builds them:
 A. per abbreviation: its long outline is one route of the word; the strokes after the base (feature strokes) are
    repeated verbatim at the end of the short outline; the route's mark keys are merged into the stroke just before
    them and no other mark key (10/15) is anywhere else in the short outline; the stroke count dropped by `saved`.
 B. per word that has an abbreviation, for every other route of the word: either it has an abbreviation, or the
    outline that the sibling's shortened base would give is taken by the stable theory / by another abbreviation
    (a legitimate loss), or it is a GAP (the outline is free yet absent: a violation).
 C. the shipped plover_stenalgo_affix_dictionary.json equals the rebuilt abbreviations (else it is stale).
"""
import json
import os
import sys
from collections import Counter

from src import affixes as A
from src.affixabbrev import Abbreviation, buildAbbreviations, loadRuleSpecs, routesOf, theoryOutlines
from src.keyboard import Starboard, Strokes
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory

KEYBOARD_JSON = "starboard3h.json"
RULES_JSON = "affix_rules.json"
SHIPPED = "plover_stenalgo_affix_dictionary.json"
MARK_KEYS = {10, 15}


def routeOutline(rec: A.WordRecord, marks: tuple[int, ...], extra: Strokes) -> Strokes:
    return A.canonicalizeStrokes(A.withMarks(rec.base, marks) + extra)


def main(argv: list[str] | None = None) -> int:
    nExamples = int(argv[argv.index("--examples") + 1]) if argv and "--examples" in argv else 0
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None or not os.path.exists(RULES_JSON):
        raise RuntimeError("run from the repo root, after util.build_affix_rules")
    phonetic, disambiguated, _w, _o = loadPhoneticAndDisambiguatedTheory(starboard)
    records, _skipped = A.extractRecords(phonetic, disambiguated)
    seedPairs, _fams = A.loadSeeds()
    pool = A.buildCandidates(records, seedPairs)
    ctx = A.SimContext(starboard, records)
    longOutline = {r.idx: A.canonicalizeStrokes(A.fullStrokesOf(r)) for r in records}
    taken = theoryOutlines(disambiguated)
    theoryWord: dict[Strokes, set[str]] = {}
    if nExamples:
        for w, outs in disambiguated.items():
            for o in outs:
                theoryWord.setdefault(A.canonicalizeStrokes(o), set()).add(w.ortho)
    abbreviations, _stats = buildAbbreviations(loadRuleSpecs(RULES_JSON), pool, ctx, taken, longOutline)

    routeOf: dict[tuple[str, Strokes], list[tuple[A.WordRecord, int]]] = {}
    for r in records:
        for ri, (marks, extra) in enumerate(routesOf(r)):
            routeOf.setdefault((r.ortho, routeOutline(r, marks, extra)), []).append((r, ri))

    errors: list[str] = []
    owner: dict[Strokes, Abbreviation] = {a.outline: a for a in abbreviations}
    byRoute: dict[tuple[int, int], Abbreviation] = {}
    for a in abbreviations:
        hits = routeOf.get((a.ortho, a.longOutline))
        if not hits:
            errors.append(f"A: {a.ortho}: long outline is not a route of the word")
            continue
        # homographs sharing an ortho and an outline are one entry in the dictionary: any of them will do
        rec, ri = hits[0]
        byRoute[(rec.idx, ri)] = a
        marks, extra = routesOf(rec)[ri]
        n = len(extra)
        s = a.outline
        if len(s) != len(a.longOutline) - a.saved:
            errors.append(f"A: {a.ortho}: {len(a.longOutline)} -> {len(s)} strokes but saved={a.saved}")
        if n and s[len(s) - n:] != extra:
            errors.append(f"A: {a.ortho} route {ri}: trailing feature strokes {s[len(s) - n:]} != {extra}")
        markStroke = s[len(s) - n - 1]
        if set(markStroke) & MARK_KEYS != set(marks):
            errors.append(f"A: {a.ortho} route {ri}: marks {sorted(set(markStroke) & MARK_KEYS)} != route's {sorted(marks)}")
        elsewhere = set().union(*s[:len(s) - n - 1]) & MARK_KEYS if len(s) - n - 1 > 0 else set()
        if elsewhere:
            errors.append(f"A: {a.ortho} route {ri}: stray mark keys {sorted(elsewhere)} in the base strokes")

    present = Counter()
    lostExamples: dict[str, list[str]] = {"theory": [], "abbreviation": []}
    gaps: list[str] = []
    potential = 0
    siblings: dict[int, list[int]] = {}
    for (idx, ri) in byRoute:
        siblings.setdefault(idx, []).append(ri)
    for idx, ris in siblings.items():
        rec = records[idx]
        routes = routesOf(rec)
        potential += len(routes) - 1
        ref = byRoute[(idx, min(ris))]
        refMarks, refExtra = routes[min(ris)]
        base = ref.outline[:len(ref.outline) - len(refExtra)]
        shortBase = base[:-1] + (tuple(sorted(set(base[-1]) - set(refMarks))),)
        for ri, (marks, extra) in enumerate(routes):
            if (idx, ri) in byRoute:
                present["has an abbreviation"] += 1
                continue
            cand = A.canonicalizeStrokes(A.withMarks(shortBase, marks) + extra)
            shown = renderFinalStrokesToRTFCRE(starboard, cand)
            mine = f"{rec.ortho} (freq {rec.frequency:.1f}) route {ri}, long {renderFinalStrokesToRTFCRE(starboard, routeOutline(rec, marks, extra))}"
            if cand in taken:
                present["lost: outline taken by the stable theory"] += 1
                if nExamples:
                    lostExamples["theory"].append(f"{mine}: wanted {shown}, which the theory gives to {sorted(theoryWord.get(cand, ()))}")
            elif cand in owner:
                o = owner[cand]
                if o.ortho == rec.ortho:
                    present["not lost: the same spelling already owns that outline"] += 1
                    continue
                present["lost: outline taken by another spelling's abbreviation"] += 1
                if o.frequency < rec.frequency:
                    present["  of which the winner is the LESS frequent spelling (primary routes go first)"] += 1
                if nExamples:
                    lostExamples["abbreviation"].append(
                        f"{mine}: wanted {shown}, kept by {o.ortho} (freq {o.frequency:.1f}, route {o.route})")
            else:
                present["GAP"] += 1
                gaps.append(f"{rec.ortho} route {ri}: {renderFinalStrokesToRTFCRE(starboard, cand)} is free but absent")
    for g in gaps:
        errors.append("B: " + g)

    rendered = {renderFinalStrokesToRTFCRE(starboard, a.outline): a.ortho for a in abbreviations}
    if os.path.exists(SHIPPED):
        with open(SHIPPED, encoding="utf-8") as f:
            shipped = json.load(f)
        if shipped != rendered:
            errors.append(f"C: {SHIPPED} differs from the rebuilt abbreviations "
                          f"({len(shipped)} vs {len(rendered)}): rerun util.export_affix_dictionary")

    byRouteCount = Counter(a.route for a in abbreviations)
    print(f"{len(abbreviations)} abbreviations: by route {dict(sorted(byRouteCount.items()))}")
    print(f"words with an abbreviation: {len(siblings)}; their routes in total: "
          f"{sum(len(routesOf(records[i])) for i in siblings)} ({potential} beyond the first)")
    for k, v in present.most_common():
        print(f"  {v:7d}  {k}")
    for kind, lines in lostExamples.items():
        lines.sort(key=lambda t: -float(t.split("freq ")[1].split(")")[0]))
        for ln in lines[:nExamples]:
            print(f"LOST to {kind}: {ln}")
    for e in errors[:40]:
        print("VIOLATION", e)
    if len(errors) > 40:
        print(f"... and {len(errors) - 40} more")
    print("OK" if not errors else f"{len(errors)} violation(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
