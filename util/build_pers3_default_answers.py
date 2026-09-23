"""
One-off transform (2026-09-19), updated after model 2 was adopted as primary
(2026-09-19): derive the pers_3-default elicitation answer set from the originally
answered one (elicitation_answers_pers1default.json, the model actually answered on the
artifact -- see pers_1PreferedOver_pers_3KeyAssignation), swapping the discrimination-
order default from pers_1 to pers_3 (nbr_s): wherever a pers_3 (singular) reading
appears in a homophone group, it becomes the silent (empty press) default instead of
pers_1/pers_2/participe. The output, elicitation_answers.json, is now the PRIMARY
answer set consumed by `python -m src.elicitation` / Discriminating-Feature Grouping
(Grouping Phase) -- model 2 (K=6) beat
model 1 (K=7) with the same 13 live markers, and the user chose to adopt it.

Mechanical rule (confirmed with the user before running):
1. Strip the 'pers_3' atom from every checked press that has it (covers both the plain
   pers_3 side and its pers_3:nbr_p plural sibling in 3-way clusters -- the plural side
   keeps whatever else it had, e.g. nbr_p).
2. Wherever this leaves the OPPOSITE side of a pers_1/pers_2 opposition with an empty
   press (it was silently relying on being the default, which pers_3 now claims), give
   it its own atom's name instead (pers_1 -> ['pers_1'], pers_2 -> ['pers_2']).
3. Re-validate against the REAL lexicon (not just the 194 questions in isolation --
   the same answer feeds many different homophone groups) using the existing E5
   machinery, and auto-repair any resulting group conflict by restoring an atom unique
   to the losing spelling's reading. Every repair is logged for review.
"""
import json
import pickle

from src.grammar import Syllable
from dictionary import Dictionary  # noqa: F401 -- needed to unpickle Dictionary.pickle
from src.elicitation import (
    AnsweredOpposition,
    buildAnswersByOpposition,
    buildLemmaHomophoneGroups,
    featureCombinationsByOrtho,
    validateElicitation,
)


def stripPers3(checked: list[str]) -> list[str]:
    return [a for a in checked if a != "pers_3"]


def transform(records: list[dict]) -> list[dict]:
    out = []
    for r in records:
        r = dict(r)  # shallow copy; checkedA/checkedB replaced below
        atomsA, atomsB = set(r["atomsA"]), set(r["atomsB"])
        checkedA, checkedB = list(r["checkedA"]), list(r["checkedB"])

        if "pers_3" in atomsA and "nbr_s" in atomsA:
            checkedA = stripPers3(checkedA)
        if "pers_3" in atomsB and "nbr_s" in atomsB:
            checkedB = stripPers3(checkedB)

        if not checkedA and ("pers_1" in atomsA or "pers_2" in atomsA):
            checkedA = ["pers_1" if "pers_1" in atomsA else "pers_2"]
        if not checkedB and ("pers_1" in atomsB or "pers_2" in atomsB):
            checkedB = ["pers_1" if "pers_1" in atomsB else "pers_2"]

        r["checkedA"], r["checkedB"] = checkedA, checkedB
        out.append(r)
    return out


def _findRecordForOpposition(records: list[dict], oppKey: frozenset) -> dict | None:
    """The one record (of the 194 distinct oppositions) whose {atomsA, atomsB} pair
    matches this exact opposition key, if any."""
    for r in records:
        if frozenset({frozenset(r["atomsA"]), frozenset(r["atomsB"])}) == oppKey:
            return r
    return None


def repairConflicts(records: list[dict], homophoneGroups: dict, maxPasses: int = 10) -> list[dict]:
    """
    Iteratively re-validate against the real lexicon and restore atoms needed to break
    any homophone-group conflict the mechanical transform introduced -- minimally: for
    each colliding spelling, find an atom unique to its own reading(s) versus the other
    colliding spellings' readings, and add it ONLY to the specific answered-opposition
    record connecting this spelling's reading to each other colliding spelling's
    reading (the one distinct opposition actually responsible), never to unrelated
    oppositions that merely happen to mention the same reading elsewhere. The same
    conflict pattern recurring across many lemmas (e.g. every regular -ir verb's
    participe vs. indicatif-présent-3s) is fixed once, since it is answered once and
    the fix -- via the elicitation model's own propagation rule -- applies everywhere
    that opposition recurs.
    """
    log: list[str] = []

    for passNum in range(maxPasses):
        answered = [
            AnsweredOpposition(
                combinationA=frozenset(r["atomsA"]), pressA=frozenset(r["checkedA"]),
                combinationB=frozenset(r["atomsB"]), pressB=frozenset(r["checkedB"]),
            )
            for r in records
        ]
        answersByOpposition, duplicates = buildAnswersByOpposition(answered)
        assert not duplicates, duplicates
        conflicts, unresolved = validateElicitation(homophoneGroups, answersByOpposition)
        assert not unresolved, f"unexpected unresolved oppositions: {unresolved[:3]}"

        if not conflicts:
            print(f"Pass {passNum}: 0 conflicts -- done.")
            break

        print(f"Pass {passNum}: {len(conflicts)} conflicts -- repairing...")
        anyFix = False
        seenOppositions: set[frozenset] = set()
        for conflict in conflicts:
            words = homophoneGroups[conflict.homophoneGroupKey]
            readingsByOrtho = featureCombinationsByOrtho(words)
            collidingOrthos = conflict.orthos
            atomsByOrtho = {
                ortho: set().union(*readingsByOrtho[ortho]) for ortho in collidingOrthos if ortho in readingsByOrtho
            }
            for ortho in collidingOrthos:
                if ortho not in atomsByOrtho:
                    continue
                otherOrthos = [o for o in collidingOrthos if o != ortho]
                otherAtoms: set[str] = set()
                for o in otherOrthos:
                    otherAtoms |= atomsByOrtho.get(o, set())
                uniqueAtoms = atomsByOrtho[ortho] - otherAtoms
                if not uniqueAtoms:
                    continue  # a genuine tie -- can't be fixed by any marker
                atomToAdd = sorted(uniqueAtoms)[0]
                for reading in readingsByOrtho[ortho]:
                    for otherOrtho in otherOrthos:
                        for otherReading in readingsByOrtho.get(otherOrtho, []):
                            if reading == otherReading:
                                continue
                            oppKey = frozenset({reading, otherReading})
                            if oppKey in seenOppositions:
                                continue
                            r = _findRecordForOpposition(records, oppKey)
                            if r is None:
                                continue  # this pairwise opposition isn't one of the 194 -- nothing to edit
                            checkedKey = "checkedA" if frozenset(r["atomsA"]) == reading else "checkedB"
                            if atomToAdd not in r[checkedKey]:
                                r[checkedKey] = r[checkedKey] + [atomToAdd]
                                log.append(
                                    f"pass {passNum}: group {conflict.homophoneGroupKey[1]} conflict on "
                                    f"press {sorted(conflict.pressSet)} ({conflict.orthos}) -- added "
                                    f"'{atomToAdd}' to {r['id']} ({r['orthoA']}/{r['orthoB']})"
                                )
                                anyFix = True
                            seenOppositions.add(oppKey)
        if not anyFix:
            print("Could not auto-repair remaining conflicts -- stopping.")
            break
    else:
        print(f"Hit maxPasses={maxPasses} without reaching zero conflicts.")

    with open("pers3default_repair_log.txt", "w", encoding="utf-8") as lf:
        lf.write("\n".join(log) + ("\n" if log else ""))
    print(f"Wrote pers3default_repair_log.txt ({len(log)} repair actions)")
    return records


def main() -> None:
    with open("Dictionary.pickle", "rb") as pfile:
        _dictionary = pickle.load(pfile)
        Syllable.allPhonemeCol = pickle.load(pfile)
        Syllable.phonemeColByPart = pickle.load(pfile)
        Syllable.biphonemeColByPart = pickle.load(pfile)
        Syllable.multiphonemeColByPart = pickle.load(pfile)
    with open("FirstTheory.pickle", "rb") as pfile:
        theory = pickle.load(pfile)
    homophoneGroups = buildLemmaHomophoneGroups(theory)

    with open("elicitation_answers_pers1default.json", encoding="utf-8") as f:
        records = json.load(f)

    transformed = transform(records)
    repaired = repairConflicts(transformed, homophoneGroups)

    with open("elicitation_answers.json", "w", encoding="utf-8") as f:
        json.dump(repaired, f, ensure_ascii=False, indent=1)
    print(f"Wrote elicitation_answers.json ({len(repaired)} entries, now primary)")


if __name__ == "__main__":
    main()
