"""
Remap the -eter/-eler verbs whose LexiqueMixte conjugation follows the RECTIFIED
1990 spelling convention from Verbiste's consonant-doubling templates to the
matching accent-grave templates, and prune the LexiqueSynthetic.tsv rows the
doubling templates generated.

Verbiste maps every -eter/-eler verb onto one of two convention pairs:
  j:eter   (jeter,   "je jette")  <->  ach:eter (acheter, "j'achète")
  app:eler (appeler, "j'appelle") <->  p:eler   (peler,   "je pèle")
The two templates of a pair differ ONLY in the alternating slots -- présent
1s/2s/3s/3p, subjonctif présent, futur, conditionnel; every other ending is
byte-identical. Which convention a verb follows is per-verb data, and the
lexicon is the source of truth: LexiqueMixte.tsv attests exactly one spelling
per form (the spelling-variant removal kept the canonical), and for 49 verbs
that surviving spelling is the rectified one (caqueter "je caquète", atteler,
étiqueter, renouveler, ...) while only the appeler/jeter family attests the
doubling. Verbiste's own mapping still assigns some of those 49 verbs a
doubling template, so Synthetic Lexicon Building (S2) generated the missing
slots with the doubled spelling ("que je caquette") beside the attested rectified
forms ("je caquète") -- perfect same-lemma homophones the Elicitation Phase
cannot separate (an unanswered subjonctif-vs-indicatif cross-spelling
opposition skips the whole group), leaving final same-lemma collisions (the 6
residuals after the B47 fix).

This script scans LexiqueMixte.tsv's attested présent/subjonctif/impératif
1s/2s/3s/3p forms of every verb Verbiste maps to a doubling template: a lemma
whose matched forms ALL follow è (at least one, none doubling) is remapped in
resources/verbiste/verbs-fr.xml to its pair's è template; a lemma attesting
any doubling form keeps Verbiste's assignment. LexiqueSynthetic.tsv rows of
remapped lemmas whose orthography is not what the è template predicts for
their slot (the doubled subjonctif/futur/conditionnel rows) are pruned, so
the S2 appenders regenerate those slots -- now spelled the rectified way --
on the next run.

Dry-run by default: prints the remaps and the rows it would prune. --apply
additionally rewrites both files.

Run: PYTHONHASHSEED=0 env/bin/python -m util.fixRectifiedEConjugations [--apply]
"""
import argparse
import csv
import re

from src.verbparadigm import (
    generateOrthoForm,
    infinitiveRadical,
    loadVerbisteTemplates,
    parseConjugationTemplates,
)

VERBS_PATH = "resources/verbiste/verbs-fr.xml"
CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
MIXTE_PATH = "resources/LexiqueMixte.tsv"
SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"

# The two convention pairs (non-alternating endings byte-identical within a
# pair -- verified against conjugations-fr.xml).
RECTIFIED_TEMPLATE_BY_DOUBLING = {"j:eter": "ach:eter", "app:eler": "p:eler"}

# Slots where the two conventions differ (the e is followed by a mute syllable).
# 1p/2p ("nous caquetons") and every imparfait/passé-simple slot are identical.
ALTERNATING_SLOTS = frozenset(
    {("ind:pre", pn) for pn in ("1s", "2s", "3s", "3p")}
    | {("sub:pre", pn) for pn in ("1s", "2s", "3s", "3p")}
    | {("imp:pre", "2s")}
)


def attestedAlternatingFormsByLemme(
    mixtePath: str,
    doublingTemplateByLemme: dict[str, str],
) -> dict[str, dict[tuple[str, str], set[str]]]:
    """
    lemma -> {alternating slot -> attested orthographies}, for the VER rows of
    lemmas Verbiste maps to a doubling -eter/-eler template. Rows whose infover
    also carries "inf" are skipped (the co-tagged-infinitive corruption, see
    attestedInfinitiveWordByLemme's docstring).
    """
    forms: dict[str, dict[tuple[str, str], set[str]]] = {}
    with open(mixtePath, encoding="utf-8") as tsvFile:
        reader = csv.reader(tsvFile, delimiter="\t")
        for row in reader:
            if len(row) < 8 or row[3] != "VER":
                continue
            lemme = row[2]
            if lemme not in doublingTemplateByLemme:
                continue
            infover = row[7]
            if not infover or "inf" in infover.split(";"):
                continue
            for tag in infover.split(";"):
                parts = tag.split(":")
                if len(parts) != 3:
                    continue
                slot = (f"{parts[0]}:{parts[1]}", parts[2])
                if slot in ALTERNATING_SLOTS:
                    forms.setdefault(lemme, {}).setdefault(slot, set()).add(row[0])
    return forms


def remappedLemmas(
    templates: dict, doublingTemplateByLemme: dict[str, str],
) -> tuple[dict[str, str], list[tuple[str, str, str, str, str]], list[str]]:
    """
    (remap, disagreements, mixed): `remap` maps each lemma Verbiste puts on a
    doubling template to that template's è counterpart, decided by the lemma's
    own attested alternating-slot forms: every matched form must follow one
    convention (a lemma attesting both spellings of one slot, or matching
    neither prediction, is reported for review instead of remapped).
    """
    rectified: dict[str, str] = {}
    doubling: dict[str, str] = {}
    disagreements: list[tuple[str, str, str, str, str]] = []
    formsByLemme = attestedAlternatingFormsByLemme(MIXTE_PATH, doublingTemplateByLemme)
    for lemme, slots in sorted(formsByLemme.items()):
        doublingId = doublingTemplateByLemme[lemme]
        rectifiedId = RECTIFIED_TEMPLATE_BY_DOUBLING[doublingId]
        radicalDoubling = infinitiveRadical(lemme, templates[doublingId])
        radicalRectified = infinitiveRadical(lemme, templates[rectifiedId])
        for (code, personNumber), orthos in sorted(slots.items()):
            for ortho in sorted(orthos):
                doubled = generateOrthoForm(radicalDoubling, templates[doublingId], code, personNumber=personNumber)
                rectifiedForm = generateOrthoForm(radicalRectified, templates[rectifiedId], code, personNumber=personNumber)
                if ortho == rectifiedForm and ortho != doubled:
                    rectified[lemme] = rectifiedId
                elif ortho == doubled and ortho != rectifiedForm:
                    doubling[lemme] = doublingId
                else:
                    disagreements.append((lemme, f"{code}:{personNumber}", ortho, doubled or "-", rectifiedForm or "-"))
    mixed = sorted(set(rectified) & set(doubling))
    for lemme in mixed:
        del rectified[lemme]
    return rectified, disagreements, mixed


def syntheticRowsToPrune(
    remap: dict[str, str], templates: dict,
) -> list[tuple[int, str, str, str]]:
    """
    LexiqueSynthetic.tsv rows (line number, lemma, ortho, infover) of remapped
    lemmas whose orthography is NOT what the lemma's new è template predicts
    for their conjugation slot -- the doubled spellings the old template
    generated. Rows whose every 3-part tag still predicts their own ortho
    (participles, imparfait, 1p/2p présent: endings identical across the
    convention pair) are kept.
    """
    pruned: list[tuple[int, str, str, str]] = []
    # newline="" keeps the file's CRLF line endings intact on read AND write --
    # the default text mode would silently rewrite the whole file as LF.
    with open(SYNTHETIC_PATH, encoding="utf-8", newline="") as tsvFile:
        for lineNumber, line in enumerate(tsvFile, start=1):
            if line.startswith("ortho\t"):
                continue
            row = line.rstrip("\r\n").split("\t")
            if len(row) < 8 or row[2] not in remap:
                continue
            lemme, ortho, infover = row[2], row[0], row[7]
            templateId = remap[lemme]
            template = templates[templateId]
            radical = infinitiveRadical(lemme, template)
            tags = [tag for tag in (infover or "").split(";") if len(tag.split(":")) == 3]
            if not tags:
                continue
            predicted = {
                generateOrthoForm(radical, template, tag.rsplit(":", 1)[0], personNumber=tag.rsplit(":", 1)[1])
                for tag in tags
            }
            if predicted != {ortho}:
                pruned.append((lineNumber, lemme, ortho, infover))
    return pruned


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--apply", action="store_true",
                        help="rewrite verbs-fr.xml and LexiqueSynthetic.tsv (default: dry run)")
    args = parser.parse_args()

    verbisteTemplates = loadVerbisteTemplates(VERBS_PATH)
    templates = parseConjugationTemplates(CONJUGATIONS_PATH)
    doublingTemplateByLemme = {
        lemme: tid for lemme, tid in verbisteTemplates.items() if tid in RECTIFIED_TEMPLATE_BY_DOUBLING
    }
    remap, disagreements, mixed = remappedLemmas(templates, doublingTemplateByLemme)

    formsByLemme = attestedAlternatingFormsByLemme(MIXTE_PATH, doublingTemplateByLemme)
    print(f"Verbs on a doubling -eter/-eler template with attested alternating forms: {len(formsByLemme)}")
    print(f"Remapped to the rectified-è templates: {len(remap)}")
    byTarget: dict[str, list[str]] = {}
    for lemme, target in remap.items():
        byTarget.setdefault(target, []).append(lemme)
    for target, lemmas in sorted(byTarget.items()):
        print(f"  -> {target}: {', '.join(sorted(lemmas))}")
    if mixed:
        print(f"NOT remapped, attest BOTH conventions (needs review): {mixed}")
    if disagreements:
        print("Forms matching neither prediction (needs review):")
        for entry in disagreements:
            print("   ", entry)

    pruned = syntheticRowsToPrune(remap, templates)
    print(f"\nLexiqueSynthetic.tsv rows to prune: {len(pruned)}")
    for lineNumber, lemme, ortho, infover in pruned:
        print(f"  line {lineNumber}: {ortho} ({lemme}, {infover})")

    if not args.apply:
        print("\nDry run; rerun with --apply to rewrite verbs-fr.xml and LexiqueSynthetic.tsv.")
        return

    with open(VERBS_PATH, encoding="utf-8") as xmlFile:
        lines = xmlFile.readlines()
    changed = 0
    for i, line in enumerate(lines):
        match = re.match(r"^<v><i>([^<]+)</i><t>([^<]+)</t>", line)
        if match and match.group(1) in remap and match.group(2) == doublingTemplateByLemme[match.group(1)]:
            lines[i] = line.replace(f"<t>{match.group(2)}</t>", f"<t>{remap[match.group(1)]}</t>", 1)
            changed += 1
    with open(VERBS_PATH, "w", encoding="utf-8") as xmlFile:
        xmlFile.writelines(lines)
    print(f"\nRewrote {VERBS_PATH}: {changed} verbs remapped.")

    pruneLineNumbers = {lineNumber for lineNumber, *_ in pruned}
    with open(SYNTHETIC_PATH, encoding="utf-8", newline="") as tsvFile:
        lines = tsvFile.readlines()
    kept = [line for i, line in enumerate(lines, start=1) if i not in pruneLineNumbers]
    with open(SYNTHETIC_PATH, "w", encoding="utf-8", newline="") as tsvFile:
        tsvFile.writelines(kept)
    print(f"Rewrote {SYNTHETIC_PATH}: {len(lines) - len(kept)} rows pruned."
          f" Rerun the S2 appenders (python -m util.build_synthetic_lexicon, or python"
          f" dictionary.py) to regenerate the slots with the rectified spellings.")


if __name__ == "__main__":
    main()
