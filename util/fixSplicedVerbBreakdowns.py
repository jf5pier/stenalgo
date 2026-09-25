#!/bin/env python
#
# Corrects item B2 in resources/LexiqueSynthetic.tsv: the finite verb forms that
# src/verbparadigm.py's generateMissingConjugatedForm synthesized before it normalized
# its spliced output (normalizeSplicedBreakdown). The splice cut the infinitive's
# phonology and syllable breakdowns at a fixed character count, which kept the
# infinitive's syllable boundaries and vowel quality: "cannes" got "k_a|n_#" (a
# vowel-less trailing syllable, one stroke more than the attested "k_a_n_#"), "abonne"
# got /abon/ (attested /abOn/), "dénie" got /denj/ (attested /deni/), and the
# orthographic breakdown's boundaries drifted from the phonemic one's.
#
# The generator now applies normalizeSplicedBreakdown to every form it builds; this
# script applies the same function, with the same tables (derived from the phonetic
# theory by deriveConjugationEndingTables), to the rows it wrote earlier. Rows are
# selected as synthetic VER rows whose every infover tag is a finite slot
# (mood:tense:person), except the pa:yer and -seoir rows, which
# util/fixPayerDualFormGaps.py and util/fixAsseoirDualFormGaps*.py write with their
# own endings (and hand rows).
#
# Dry-run by default: only reads and reports. --apply writes the corrected phon,
# syll_cv and orthosyll_cv fields back into the matching rows in place, keeping every
# row's own line ending. Rerun Synthetic Lexicon Building (S2) afterwards (with the
# pickles deleted): the corrected phonology changes the theory its gating reads.
import argparse
import collections
import csv
import sys

from src.verbparadigm import (
    deriveConjugationEndingTables,
    loadVerbisteTemplates,
    loadVerbModelExceptions,
    normalizeSplicedBreakdown,
)
from util.completeVerbParadigms import (
    EXCEPTIONS_PATH,
    VERBISTE_VERBS_PATH,
    _capMemory,
    loadTheoryAndKeyboard,
)

LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
OWN_ENDINGS_TEMPLATES = {"pa:yer"}
OWN_ENDINGS_LEMME_SUFFIX = "seoir"


def isSplicedFiniteRow(row: dict[str, str], verbisteTemplates: dict[str, str]) -> bool:
    tags = [tag for tag in row["infover"].split(";") if tag]
    return (
        row["cgram"] == "VER"
        and bool(tags) and all(len(tag.split(":")) == 3 for tag in tags)
        and verbisteTemplates.get(row["lemme"]) not in OWN_ENDINGS_TEMPLATES
        and not row["lemme"].endswith(OWN_ENDINGS_LEMME_SUFFIX)
    )


def main() -> None:
    _capMemory()
    parser = argparse.ArgumentParser(
        description="Re-normalize the phonology and syllable breakdowns of the spliced "
        "finite verb rows of resources/LexiqueSynthetic.tsv (item B2)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to resources/LexiqueSynthetic.tsv (default: dry-run).",
    )
    args = parser.parse_args()

    print("Loading theory (uses PhoneticTheory.pickle if present)...")
    theory, _starboard = loadTheoryAndKeyboard()
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)

    with open(LEXIQUE_SYNTHETIC_PATH, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\r\n").split("\t")
    fieldIdx = {name: header.index(name) for name in header}
    phonIdx, syllIdx, orthoIdx = fieldIdx["phon"], fieldIdx["syll_cv"], fieldIdx["orthosyll_cv"]

    changedFields: collections.Counter[str] = collections.Counter()
    examples: list[str] = []
    selected = modified = 0
    for i in range(1, len(lines)):
        body = lines[i].rstrip("\r\n")
        if not body.strip():
            continue
        ending = lines[i][len(body):]
        fields = body.split("\t")
        row = dict(zip(header, fields))
        if not isSplicedFiniteRow(row, verbisteTemplates):
            continue
        selected += 1
        old = (fields[phonIdx], fields[syllIdx], fields[orthoIdx])
        new = normalizeSplicedBreakdown(
            *old, tables.syllableSplitByCluster, tables.midVowelByOrtho
        )
        if new == old:
            continue
        modified += 1
        for name, before, after in zip(("phon", "syll_cv", "orthosyll_cv"), old, new):
            if before != after:
                changedFields[name] += 1
        if len(examples) < 25:
            examples.append(f"  {row['ortho']:<16} {row['infover']:<14} {old} -> {new}")
        fields[phonIdx], fields[syllIdx], fields[orthoIdx] = new
        lines[i] = "\t".join(fields) + ending

    print(f"Spliced finite rows: {selected}; corrected: {modified} "
          f"(phon {changedFields['phon']}, syll_cv {changedFields['syll_cv']}, "
          f"orthosyll_cv {changedFields['orthosyll_cv']})")
    print("\n".join(examples))

    if not modified:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)
    if args.apply:
        with open(LEXIQUE_SYNTHETIC_PATH, "w", newline="") as f:
            f.writelines(lines)
        print(f"--apply: wrote {modified} corrected rows to {LEXIQUE_SYNTHETIC_PATH}")


if __name__ == "__main__":
    main()
