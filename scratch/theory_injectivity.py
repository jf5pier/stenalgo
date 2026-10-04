"""Step 3 of PLAN_2026-10-04-expression-decoder.md: whole-theory injectivity of the attach merge.
Every theory outline (and every brief) is a host for every selected attach rule and every
disjoint stack of two; counts shadows (merged outline == a live outline of another word or a
brief), collisions (two different (stack, host) pairs, or a swallowed selector, give one outline)
and refusals (overlap / illegal union), with host frequency mass.
Scope: single rules on the first/last stroke of every host, same-side pairs on multi-stroke hosts,
any pair on one-stroke hosts. Cross-side collisions between multi-stroke hosts (prefix merge on X
== suffix merge on Y) are NOT searched.
Usage: PYTHONPATH=. env/bin/python scratch/theory_injectivity.py"""

from __future__ import annotations

import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.decode_roundtrip import loadAll  # noqa: E402
from src.affixes import PREFIX  # noqa: E402
from src.elision import elisionAgrees  # noqa: E402
from src.keyboard import canonicalizeStrokes  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402
from src.keyboard import Starboard  # noqa: E402

MARKS = (1 << 10) | (1 << 15)


def mask(stroke) -> int:
    m = 0
    for k in stroke:
        m |= 1 << k
    return m


def main() -> None:
    ctx, rules, pool, words, unitStrokes = loadAll()
    starboard = Starboard.fromJSONFile("starboard3h.json")
    theory = loadDisambiguatedTheory(starboard)
    freq: dict = defaultdict(float)
    label: dict = {}
    for w, alts in theory.items():
        for s in alts:
            o = tuple(mask(st) for st in canonicalizeStrokes(s))
            freq[o] += w.frequency
            label.setdefault(o, w.ortho)
    hosts = dict(freq)                              # outline -> frequency
    live = set(hosts)
    for b in rules.briefs:
        o = tuple(mask(st) for st in canonicalizeStrokes(b.strokes))
        label.setdefault(o, "BRIEF:" + " ".join(b.expression))
        hosts.setdefault(o, 0.0)
        live.add(o)
    print(f"hosts {len(hosts)} (words {len(freq)} + briefs), total frequency {sum(freq.values()):.3e}")

    orthosOf: dict = defaultdict(set)
    for o, ws in words.items():
        orthosOf[tuple(mask(st) for st in canonicalizeStrokes(o))] |= set(ws)

    def agrees(elision: str, outline) -> bool:
        """Elision pair (shared chord): the merge exists only if some word of the host outline
        fits the form (the composer refuses the rest, the decoder never reads them)."""
        return not elision or any(elisionAgrees(elision, w) for w in orthosOf.get(outline, ()))

    legalCache: dict[int, bool] = {}

    def legal(m: int) -> bool:
        v = legalCache.get(m)
        if v is None:
            keys = tuple(k for k in range(64) if (m >> k) & 1 and (1 << k) & MARKS == 0)
            v = legalCache[m] = ctx.isLegal(keys)
        return v

    atts = [(" ".join(r.expression) + ("<" if r.position == PREFIX else ">"), r.position, mask(r.keypress),
             mask(r.keypress) & ~MARKS, r.elision) for r in rules.attaches]
    stacks: list[tuple[str, frozenset[str], int, int, tuple[str, ...]]] = [
        (n, frozenset([p]), km, sm, (el,) if el else ()) for n, p, km, sm, el in atts]
    for (n1, p1, k1, s1, e1), (n2, p2, k2, s2, e2) in combinations(atts, 2):
        if s1 & s2 == 0:
            stacks.append((n1 + " + " + n2, frozenset([p1, p2]), k1 | k2, s1 | s2,
                           tuple(e for e in (e1, e2) if e)))
    nSingles = len(atts)
    print(f"{nSingles} rules, {len(stacks) - nSingles} disjoint pairs")

    stat: dict = defaultdict(lambda: defaultdict(float))     # label -> counters

    def tally(name: str, key: str, hostFreq: float) -> None:
        kind = "single" if name in single else "pair"
        for k in (name, "ALL " + kind):
            stat[k][key] += 1
            stat[k][key + "_mass"] += hostFreq

    single = {n for n, *_ in stacks[:nSingles]}

    # groups: key -> list of (outline, index of the stroke the stack merges into)
    groups: dict = defaultdict(list)
    for o in hosts:
        if len(o) == 1:
            groups[("one",)].append((o, 0))
        else:
            groups[("P", o[1:])].append((o, 0))
            groups[("S", o[:-1])].append((o, len(o) - 1))

    shadowedWords: dict = defaultdict(float)
    examples: dict = defaultdict(list)
    for gkey, members in groups.items():
        side = gkey[0]
        readings: dict = defaultdict(list)                   # composed outline -> [(stack name, host outline)]
        for o, idx in members:
            h = o[idx]
            for name, positions, km, sm, forms in stacks:
                if side == "P" and positions != {PREFIX}:
                    continue
                if side == "S" and PREFIX in positions:
                    continue
                if side == "one" or True:
                    pass
                if forms and not all(agrees(f, o) for f in forms):
                    continue
                if h & sm:
                    tally(name, "refusedOverlap", hosts[o])
                    continue
                u = h | km
                if not legal(u):
                    tally(name, "refusedIllegal", hosts[o])
                    continue
                composed = o[:idx] + (u,) + o[idx + 1:]
                tally(name, "mergeable", hosts[o])
                readings[composed].append((name, o))
        for composed, rs in readings.items():
            isLive = composed in live
            if isLive:
                for name, o in rs:
                    tally(name, "shadow", hosts[o])
                    shadowedWords[composed] = hosts.get(composed, 0.0)
                    if len(examples[name]) < 3:
                        examples[name].append(f"{label[o]} -> {label[composed]}")
            if len(rs) > 1:
                for name, o in rs:
                    tally(name, "collision", hosts[o])
                    if len(examples[name + "#c"]) < 3:
                        examples[name + "#c"].append(" | ".join(f"{n}:{label[x]}" for n, x in rs[:3]))

    total = sum(freq.values())
    print("\nper single rule (host counts; mass = host frequency, fraction of the whole theory's frequency)")
    for n in sorted(single, key=lambda n: -stat[n]["mergeable_mass"]):
        s = stat[n]
        print(f"{n:12} mergeable {int(s['mergeable']):6} refused {int(s['refusedOverlap'] + s['refusedIllegal']):6} "
              f"shadow {int(s['shadow']):5} ({100 * s['shadow_mass'] / total:.3f}%) "
              f"collision {int(s['collision']):5} ({100 * s['collision_mass'] / total:.3f}%)"
              + (f"   e.g. {examples[n][:2]}" if examples[n] else ""))
    for k in ("ALL single", "ALL pair"):
        s = stat[k]
        print(f"\n{k}: mergeable {int(s['mergeable'])}, overlap {int(s['refusedOverlap'])}, illegal {int(s['refusedIllegal'])}, "
              f"shadow {int(s['shadow'])} (mass {100 * s['shadow_mass'] / total:.3f}% of theory frequency per merge), "
              f"collision {int(s['collision'])} (mass {100 * s['collision_mass'] / total:.3f}%)")
    pairs = [n for n in stat if " + " in n and not n.startswith("ALL") and not n.endswith("#c")]
    print("\ntop pairs by shadow+collision count:")
    for n in sorted(pairs, key=lambda n: -(stat[n]["shadow"] + stat[n]["collision"]))[:10]:
        print(f"  {n:28} mergeable {int(stat[n]['mergeable']):6} shadow {int(stat[n]['shadow']):5} collision {int(stat[n]['collision']):5}")

    # attach chords and forced briefs against live outlines
    print("\nattach chords against live single-stroke outlines / briefs:")
    briefOutlines = {mask(b.strokes[0]): " ".join(b.expression) for b in rules.briefs if len(b.strokes) == 1}
    for r in rules.attaches:
        m = mask(r.keypress)
        base = m & ~MARKS
        hits = []
        if (m,) in live:
            hits.append("live:" + label[(m,)])
        if m in briefOutlines:
            hits.append("brief:" + briefOutlines[m])
        if base != m and (base,) in live:
            hits.append("base-live:" + label[(base,)])
        if hits:
            print(f"  {' '.join(r.expression):10} {hits}")


if __name__ == "__main__":
    main()
