#!/bin/env python
#
# Batch 9/10 (residual small template defects) of the lexicon-defect triage
# plan: three independent, one-off fixes in
# resources/verbiste/conjugations-fr.xml, each confirmed against the actual
# attested lexicon rows before fixing (not guessed):
#
#   - dép:ecer: présent/futur-simple/conditionnel:présent/subjonctif-présent/
#     imperatif already have BOTH "e" and "è" <i> alternatives, but list the
#     unaccented "e"-form first (primary). Every attested "dépecer" row in
#     resources/LexiqueMixte.tsv that hits a stressed slot uses the "è"-form
#     exclusively (dépèce, dépècent, dépècera, dépècerait, ...) -- no
#     unaccented counterpart is ever attested for these slots (single-answer
#     case, unlike -ayer/ass:eoir) -- so this is the same class of fix as the
#     already-applied l:éguer/harc:eler reorderings: swap "è" to primary.
#   - préd:ire: présent/imperatif "vous" slot lists <i>ites</i><i>isez</i> --
#     the irregular "dire"-style "-dites" ending is only correct for "dire"
#     itself and "redire" (both mapped to their own "d:ire" template in
#     resources/verbiste/verbs-fr.xml); every lemma actually assigned
#     préd:ire (contredire, dédire, prédire -- confirmed via verbs-fr.xml;
#     interdire/médire use their own separate interd:ire/méd:ire templates)
#     regularly conjugates "-disez" (contredisez, prédisez), matching every
#     attested row. Swap "isez" to primary.
#   - l:éser: subjonctif-présent 1p is a straight typo, "ésrions" (not a real
#     French ending) instead of "ésions" -- confirmed against l:éser's own
#     imparfait 1p ("ésions") and every sibling template's parallel slot
#     (c:éder's "édions", l:éguer's "éguions", diss:équer's "équions" all
#     follow the same unstressed-1p pattern). Direct typo fix, no reordering.
#
# Dry-run by default: only reads and reports. --apply rewrites the affected
# <p> elements in resources/verbiste/conjugations-fr.xml, in place.
# Idempotent: a no-op (0 corrections needed) if run again after a successful
# --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"

# (templateName, [(old, new, expectedCount), ...])
DEPECER_CORRECTIONS = [
    ("<p><i>ece</i><i>èce</i></p>", "<p><i>èce</i><i>ece</i></p>", 5),
    ("<p><i>eces</i><i>èces</i></p>", "<p><i>èces</i><i>eces</i></p>", 2),
    ("<p><i>ecent</i><i>ècent</i></p>", "<p><i>ècent</i><i>ecent</i></p>", 2),
    ("<p><i>ecerai</i><i>ècerai</i></p>", "<p><i>ècerai</i><i>ecerai</i></p>", 1),
    ("<p><i>eceras</i><i>èceras</i></p>", "<p><i>èceras</i><i>eceras</i></p>", 1),
    ("<p><i>ecera</i><i>ècera</i></p>", "<p><i>ècera</i><i>ecera</i></p>", 1),
    ("<p><i>ecerons</i><i>ècerons</i></p>", "<p><i>ècerons</i><i>ecerons</i></p>", 1),
    ("<p><i>ecerez</i><i>ècerez</i></p>", "<p><i>ècerez</i><i>ecerez</i></p>", 1),
    ("<p><i>eceront</i><i>èceront</i></p>", "<p><i>èceront</i><i>eceront</i></p>", 1),
    ("<p><i>ecerais</i><i>ècerais</i></p>", "<p><i>ècerais</i><i>ecerais</i></p>", 2),
    ("<p><i>ecerait</i><i>ècerait</i></p>", "<p><i>ècerait</i><i>ecerait</i></p>", 1),
    ("<p><i>ecerions</i><i>ècerions</i></p>", "<p><i>ècerions</i><i>ecerions</i></p>", 1),
    ("<p><i>eceriez</i><i>èceriez</i></p>", "<p><i>èceriez</i><i>eceriez</i></p>", 1),
    ("<p><i>eceraient</i><i>èceraient</i></p>", "<p><i>èceraient</i><i>eceraient</i></p>", 1),
]

PREDIRE_CORRECTIONS = [
    ("<p><i>ites</i><i>isez</i></p>", "<p><i>isez</i><i>ites</i></p>", 2),
]

LESER_CORRECTIONS = [
    ("<p><i>ésrions</i></p>", "<p><i>ésions</i></p>", 1),
]

TEMPLATES: dict[str, list[tuple[str, str, int]]] = {
    "dép:ecer": DEPECER_CORRECTIONS,
    "préd:ire": PREDIRE_CORRECTIONS,
    "l:éser": LESER_CORRECTIONS,
}


def extractTemplateBlock(content: str, templateName: str) -> tuple[str, int, int]:
    pattern = re.compile(
        r'<template name="' + re.escape(templateName) + r'">.*?</template>',
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one <template name={templateName!r}> "
                          f"block, found {len(matches)}")
    m = matches[0]
    return m.group(0), m.start(), m.end()


def buildCorrectedBlock(block: str, corrections: list[tuple[str, str, int]]
                         ) -> tuple[str, int, list[str]]:
    corrected = block
    applied = 0
    warnings: list[str] = []
    for old, new, expectedCount in corrections:
        count = corrected.count(old)
        if count == 0:
            warnings.append(f"expected {expectedCount} occurrence(s) of {old!r}, found 0")
            continue
        if count != expectedCount:
            warnings.append(f"expected {expectedCount} occurrence(s) of {old!r}, found {count}")
        corrected = corrected.replace(old, new)
        applied += count
    return corrected, applied, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix three independent residual template defects: "
        "dép:ecer's unaccented-primary ordering, préd:ire's wrong 'vous' "
        "ending, and l:éser's subjonctif:présent 1p typo."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to resources/verbiste/conjugations-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    totalApplied = 0
    for templateName, corrections in TEMPLATES.items():
        block, start, end = extractTemplateBlock(content, templateName)
        correctedBlock, applied, warnings = buildCorrectedBlock(block, corrections)

        print(f"=== {templateName} ===")
        for old, new, expectedCount in corrections:
            if old in block:
                print(f"  {old} -> {new}  (x{expectedCount})")
        print(f"<p> texts corrected: {applied}")
        for w in warnings:
            print(f"  WARNING: {w}")
        print()

        if args.apply and applied:
            content = content[:start] + correctedBlock + content[end:]
            totalApplied += applied

    if args.apply:
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"--apply: wrote corrections ({totalApplied} <p> texts) to {CONJUGATIONS_PATH}")


if __name__ == "__main__":
    main()
