"""
Validate elicited conjugation/gender-number presses against the user-authored spec in
`conjugation_disambiguation_order.txt`: an ordered vocabulary of marker combinations,
earlier entries requiring fewer features to discriminate, plus two special rules:

- A masculine reading ("m" or "m s") is always the cluster's free (empty-press) default
  -- it must never require an explicit press.
- An impératif reading's press, whenever non-empty, must be exactly {"impératif"} (not
  combined with anything else) -- impératif's three conjugations never phonologically
  collide with each other, so the bare marker alone is always both necessary and
  sufficient.
- A subjonctif reading's press, whenever non-empty, must be exactly {"subjonctif"}.

This is a REPORT only (per the 2026-09-22 decision) -- it does not modify
`elicitation_answers.json` or `resolved_press_sets.json`; a violation means the
underlying elicitation answer (or, rarer, the lexicon itself) needs a human look, not
that this script should silently override it.

Run: python -m util.check_conjugation_disambiguation_order
Requires Dictionary.pickle/FirstTheory.pickle (`python dictionary.py` first) and
elicitation_answers.json.
"""
import json
import os
import pickle
from dataclasses import dataclass

from dictionary import Dictionary  # noqa: F401 -- needed to unpickle Dictionary.pickle
from src.elicitation import (
    AnsweredOpposition, buildAnswersByOpposition, buildLemmaHomophoneGroups,
    featureCombinationsByOrtho, resolvePressByCombination,
)
from src.grammar import Syllable
from src.word import WordOrtho

SPEC_PATH = "conjugation_disambiguation_order.txt"
REPORT_PATH = "conjugation_disambiguation_report.json"

_TOKEN_ALIASES = {"imperatif": "impératif"}
_IGNORED_TOKENS = {"simple"}


def parsePrecedenceOrder(path: str = SPEC_PATH) -> list[frozenset[str]]:
    """The doc's ordered vocabulary (line order = precedence, earlier = fewer features),
    stopping at the "-----" separator before the free-text special rules section."""
    order: list[frozenset[str]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("---") or stripped.lower().startswith("special rules"):
                break
            if not stripped or stripped.startswith("Exhaustive") or stripped.startswith("$and"):
                continue
            tokens = [_TOKEN_ALIASES.get(t, t) for t in stripped.split() if t not in _IGNORED_TOKENS]
            if tokens:
                order.append(frozenset(tokens))
    return order


GENDER_NUMBER_ATOMS = frozenset({"m", "f", "s", "p"})


def classifyCombination(combination: frozenset[str]) -> str:
    """Which of `conjugation_disambiguation_order.txt`'s rule families a reading's full
    feature combination belongs to -- classification ignores the constant backdrop tags
    ("participe"/"VER"/gender-number's own "passé") a Word's combination always carries
    alongside the atoms that actually vary within its cluster (see
    `src.elicitation.wordFeatureCombinations`)."""
    if "participe" in combination:
        return "gender_number"
    if combination == frozenset({"infinitif"}):
        return "infinitif"
    if "impératif" in combination:
        return "impératif"
    if "subjonctif" in combination:
        return "subjonctif"
    return "finite_verb"


@dataclass
class Violation:
    rule: str
    lemmeGramCat: str
    ortho: WordOrtho
    combination: frozenset[str]
    actualPress: frozenset[str]
    expectedPress: frozenset[str] | None


def checkPressByOrthoCombination(
    pressByOrthoCombinationByGroup: dict, orthoLemmeGramCatByGroupKey: dict[tuple, str],
) -> tuple[list[Violation], set[str]]:
    violations: list[Violation] = []
    seenAtoms: set[str] = set()
    for groupKey, pressByOrthoCombination in pressByOrthoCombinationByGroup.items():
        lemmeGramCat = orthoLemmeGramCatByGroupKey[groupKey]
        for (ortho, combination), press in pressByOrthoCombination.items():
            seenAtoms |= press
            kind = classifyCombination(combination)
            if kind == "gender_number":
                genderNumber = combination & GENDER_NUMBER_ATOMS
                if genderNumber <= {"m", "s"} and press:
                    violations.append(Violation(
                        "masculine_must_be_free", lemmeGramCat, ortho, combination, press, frozenset()
                    ))
            elif kind == "impératif" and press and press != frozenset({"impératif"}):
                violations.append(Violation(
                    "imperatif_must_be_exactly_itself", lemmeGramCat, ortho, combination, press,
                    frozenset({"impératif"}),
                ))
            elif kind == "infinitif" and press and press != frozenset({"infinitif"}):
                violations.append(Violation(
                    "infinitif_must_be_exactly_itself", lemmeGramCat, ortho, combination, press,
                    frozenset({"infinitif"}),
                ))
            elif kind == "subjonctif" and press:
                extra = press - {"subjonctif"}
                validShape = (
                    "subjonctif" in press and len(extra) <= 1
                    and all(atom.startswith("pers_") or atom.startswith("nbr_") for atom in extra)
                )
                if not validShape:
                    violations.append(Violation(
                        "subjonctif_mandatory_with_at_most_one_pers_or_nbr_clarifier",
                        lemmeGramCat, ortho, combination, press, None,
                    ))
    return violations, seenAtoms


def main() -> None:
    if not os.path.exists("Dictionary.pickle") or not os.path.exists("FirstTheory.pickle"):
        raise RuntimeError("Run `python dictionary.py` first to build Dictionary.pickle / FirstTheory.pickle.")
    if not os.path.exists("elicitation_answers.json"):
        raise RuntimeError("elicitation_answers.json not found -- nothing to validate.")

    precedenceOrder = parsePrecedenceOrder()
    vocabulary = {atom for combination in precedenceOrder for atom in combination}

    with open("Dictionary.pickle", "rb") as pfile:
        pickle.load(pfile)  # _dictionary, unused here
        Syllable.allPhonemeCol = pickle.load(pfile)
        Syllable.phonemeColByPart = pickle.load(pfile)
        Syllable.biphonemeColByPart = pickle.load(pfile)
        Syllable.multiphonemeColByPart = pickle.load(pfile)
    with open("FirstTheory.pickle", "rb") as pfile:
        theory = pickle.load(pfile)

    homophoneGroups = buildLemmaHomophoneGroups(theory)
    orthoLemmeGramCatByGroupKey = {key: key[1] for key in homophoneGroups}

    with open("elicitation_answers.json", encoding="utf-8") as af:
        answerRecords = json.load(af)
    answeredOppositions = [
        AnsweredOpposition(
            combinationA=frozenset(rec["atomsA"]), pressA=frozenset(rec["checkedA"]),
            combinationB=frozenset(rec["atomsB"]), pressB=frozenset(rec["checkedB"]),
        )
        for rec in answerRecords
    ]
    answersByOpposition, _duplicates = buildAnswersByOpposition(answeredOppositions)
    pressByOrthoCombinationByGroup, _unresolved = resolvePressByCombination(homophoneGroups, answersByOpposition)

    violations, seenAtoms = checkPressByOrthoCombination(pressByOrthoCombinationByGroup, orthoLemmeGramCatByGroupKey)
    unknownAtoms = seenAtoms - vocabulary

    print("=== conjugation_disambiguation_order.txt validation ===")
    print(f"Precedence entries parsed: {len(precedenceOrder)}, vocabulary: {len(vocabulary)} atoms")
    print(f"Groups checked: {len(pressByOrthoCombinationByGroup)}")
    byRule: dict[str, int] = {}
    for v in violations:
        byRule[v.rule] = byRule.get(v.rule, 0) + 1
    print(f"Violations: {len(violations)}")
    for rule, count in sorted(byRule.items()):
        print(f"  {rule}: {count}")
    if unknownAtoms:
        print(f"Atoms elicited but absent from the spec's vocabulary: {sorted(unknownAtoms)}")

    if violations:
        print("\nSample violations (up to 15 per rule):")
        shown: dict[str, int] = {}
        for v in violations:
            if shown.get(v.rule, 0) >= 15:
                continue
            shown[v.rule] = shown.get(v.rule, 0) + 1
            print(f"  [{v.rule}] {v.ortho} ({v.lemmeGramCat}) combination={sorted(v.combination)} "
                  f"press={sorted(v.actualPress)} expected={sorted(v.expectedPress or [])}")

    with open(REPORT_PATH, "w", encoding="utf-8") as rf:
        json.dump({
            "precedenceEntryCount": len(precedenceOrder),
            "vocabulary": sorted(vocabulary),
            "groupsChecked": len(pressByOrthoCombinationByGroup),
            "violationCountByRule": byRule,
            "unknownAtoms": sorted(unknownAtoms),
            "violations": [
                {
                    "rule": v.rule, "lemmeGramCat": v.lemmeGramCat, "ortho": v.ortho,
                    "combination": sorted(v.combination), "actualPress": sorted(v.actualPress),
                    "expectedPress": sorted(v.expectedPress or []),
                }
                for v in violations
            ],
        }, rf, ensure_ascii=False, indent=1)
    print(f"\nWrote {REPORT_PATH} ({len(violations)} violations).")


if __name__ == "__main__":
    main()
