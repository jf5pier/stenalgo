"""
One-off transform (2026-09-19): derive a second elicitation answer set from the live one
(elicitation_answers.json), swapping the discrimination-order default from pers_1 (the
model actually answered on the artifact -- see pers_1PreferedOver_pers_3KeyAssignation)
to pers_3 (nbr_s): wherever a pers_3 (singular) reading appears in a homophone group, it
becomes the silent (empty press) default instead of pers_1/pers_2/participe.

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


def repairConflicts(records: list[dict], homophoneGroups: dict, maxPasses: int = 10) -> list[dict]:
    """Iteratively re-validate against the real lexicon and restore atoms needed to
    break any homophone-group conflict the mechanical transform introduced. For each
    colliding spelling, find an atom unique to its own reading(s) versus the other
    colliding spellings' readings, and add it wherever that exact reading is answered
    against anything (safe even if broader than the minimal single opposition
    responsible -- over-specific presses are explicitly tolerated by the plan)."""
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
                    for r in records:
                        for atomsKey, checkedKey in (("atomsA", "checkedA"), ("atomsB", "checkedB")):
                            if frozenset(r[atomsKey]) == reading and atomToAdd not in r[checkedKey]:
                                r[checkedKey] = r[checkedKey] + [atomToAdd]
                                log.append(
                                    f"pass {passNum}: group {conflict.homophoneGroupKey[1]} conflict on "
                                    f"press {sorted(conflict.pressSet)} ({conflict.orthos}) -- added "
                                    f"'{atomToAdd}' to {r['id']} side matching reading of '{ortho}'"
                                )
                                anyFix = True
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

    with open("elicitation_answers.json", encoding="utf-8") as f:
        records = json.load(f)

    transformed = transform(records)
    repaired = repairConflicts(transformed, homophoneGroups)

    with open("elicitation_answers_pers3default.json", "w", encoding="utf-8") as f:
        json.dump(repaired, f, ensure_ascii=False, indent=1)
    print(f"Wrote elicitation_answers_pers3default.json ({len(repaired)} entries)")


if __name__ == "__main__":
    main()
