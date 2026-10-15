"""Fusing a rare phoneme with another one of the same syllabic part (both use the same keys), in the full final theory.

Rare = phoneme variant whose removal creates, at S7, < 100 colliding groups or < 1000 colliding frequency (the literal rule
is 100/100; `literal` marks those), from out/phoneme_information_raw.tsv.
For a rare phoneme P and a partner Q of the same part, two exchanges are evaluated on the final theory
(merged outlines + affix + brief dictionaries; the intact theory has 0 collisions there):
  P->Q : every P of that part is typed with Q's keys        Q->P : every Q of that part is typed with P's keys
Feature, mark and merge keys stay as they are (no re-disambiguation). Collisions are counted only among the affected outlines
(exact, since the intact theory has none): colliding groups and non-top frequency mass.
Output: out/phoneme_fusion.tsv
"""
import csv
import os
import sys
from collections import defaultdict
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optexp_phoneme_information as m  # noqa: E402
from optexp_common import OUT  # noqa: E402

G = m.G
PARTS = ("onset", "nucleus", "coda")
CONSONANT_ONLY: set[str] = set()


def rare(wordsMax: int = 100, massMax: float = 1000.0) -> list[tuple[str, str, bool]]:
    """(phoneme, part, meets the literal 100/100 rule) of every phoneme variant whose removal creates, at S7,
    fewer than `wordsMax` colliding groups (the collision count the md table shows) or less than `massMax` colliding frequency. Consonants by onset/coda variant,
    vowels by their plain label (nucleus). The literal rule is groups < 100 or mass < 100."""
    out = []
    for r in csv.DictReader(open(os.path.join(OUT, "phoneme_information_raw.tsv")), delimiter="\t"):
        if r["stage"] != "S7_marks" or r["phoneme"] == "(intact)":
            continue
        ph, _, part = r["phoneme"].partition("/")
        w, f = int(r["groups"]), float(r["excessFreq"])
        if not part:
            if ph in CONSONANT_ONLY:
                continue
            part = "nucleus"
        if w < wordsMax or f < massMax:
            out.append((ph, part, w < 100 or f < 100))
    return out


def substituted(i: int, part: str, src: str, dst: str) -> tuple[Any, Any]:
    kb = G["kb"]
    new = []
    for syl in G["wParts"][i]:
        parts = {p: ([dst if x == src else x for x in phs] if p == part else list(phs)) for p, phs in syl.items()}
        new.append(frozenset(kb.getStrokeOfSyllableByPart(parts)))
    return G["wBase"][i], tuple(new)


def exchange(index: dict[Any, list[Any]], part: str, src: str, dst: str, changed: list[int]) -> dict[str, float]:
    cset = set(changed)
    fresh: dict[Any, list[Any]] = defaultdict(list)
    affected = set()
    for i in changed:
        old, new = substituted(i, part, src, dst)
        for o in G["stageOut"]["merged"][i]:
            affected.add(o)
        for o in G["stageOut"]["merged"][i]:
            r = m.remap(o, old, new)
            if r:
                affected.add(r)
                fresh[r].append((r, G["wOrtho"][i], G["wFreq"][i], G["wLemma"][i]))
    claims = []
    for o in affected:
        claims.extend(c for c in index.get(o, []) if not (c[4] == "w" and c[5] in cset))
        claims.extend(fresh.get(o, []))
    r = m.collisions([c[:4] for c in claims])
    return {"groups": r["groups"], "mass": r["excessFreq"]}


def main() -> None:
    m.prepare()
    index: dict[Any, list[Any]] = defaultdict(list)
    for i, outs in enumerate(G["stageOut"]["merged"]):
        for o in outs:
            index[o].append((o, G["wOrtho"][i], G["wFreq"][i], G["wLemma"][i], "w", i))
    for name in ("plus_affix", "plus_briefs"):
        for o, ortho in G["fixed"][name]:
            index[o].append((o, ortho, G["orthoFreq"].get(ortho, 0.0), "\0fixed" + str(ortho), "f", -1))
    byPart: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, parts in enumerate(G["wParts"]):
        for part in PARTS:
            for ph in {p for syl in parts for p in syl[part]}:
                byPart[(ph, part)].append(i)
    kb = G["kb"]
    CONSONANT_ONLY.update(p for (p, pt) in byPart if pt != "nucleus" and not any(k == (p, "nucleus") for k in byPart))
    rows = []
    for ph, part, literal in rare():
        for q in sorted(p for (p, pt) in byPart if pt == part and p != ph):
            try:
                kb.getStrokesOfPhoneme(q, part)[0]
                kb.getStrokesOfPhoneme(ph, part)[0]
            except Exception:
                continue
            a = exchange(index, part, ph, q, byPart[(ph, part)])
            b = exchange(index, part, q, ph, byPart[(q, part)])
            rows.append({"literal": int(literal), "phoneme": ph, "part": part, "partner": q, "keysP": kb.getStrokesOfPhoneme(ph, part)[0],
                         "keysQ": kb.getStrokesOfPhoneme(q, part)[0], "wordsP": len(byPart[(ph, part)]),
                         "wordsQ": len(byPart[(q, part)]), "P_to_Q_groups": a["groups"], "P_to_Q_mass": round(a["mass"], 1),
                         "Q_to_P_groups": b["groups"], "Q_to_P_mass": round(b["mass"], 1)})
            print(rows[-1], flush=True)
    with open(os.path.join(OUT, "phoneme_fusion.tsv"), "w", newline="") as f:
        wr = csv.DictWriter(f, list(rows[0]), delimiter="\t")
        wr.writeheader()
        wr.writerows(rows)


if __name__ == "__main__":
    main()
