#!/bin/env python
#
# Corrects item B46 in resources/LexiqueSynthetic.tsv: the past participles that
# src/verbparadigm.py's generateMissingParticiple synthesized while its phonemic
# splice (spliceParticiplePhon) still dropped every '#' unit while the
# orthographic splice (generateParticipeOrthosyll) appended the gender/number
# suffix as an extra unit. 4,829 rows are one orthographic unit short
# ("globalisés" g_l_O|b_a|l_i|z_e beside g_l_o|b_a|l_i|s_é_s; attested convention:
# g_l_O|b_a|l_i|z_e_#), 91 two (the silent "h" of "inhumées" is its own
# orthographic unit), 294 already aligned.
#
# The fix is row-local: append one silent trailing "_#" per missing orthographic
# unit to syll_cv, exactly what the generator's _padSilentUnits now produces.
# The phoneme string is unchanged ("#" is stripped before building it), but the
# unit-aligned readers (deriveSyllableSplitTable, deriveMidVowelTable,
# normalizeSplicedBreakdown's orthographic copy) stop skipping these rows.
#
# Dry-run by default: only reads and reports. --apply rewrites the syll_cv field
# in place (keeping every row's own line ending). Rerun Synthetic Lexicon
# Building (S2) afterwards, with the pickles deleted.
import argparse
import collections
import csv
import sys

from src.verbparadigm import _padSilentUnits

LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"


def isParticipleRow(row: dict[str, str]) -> bool:
    return (
        row["cgram"] == "VER" and "par:pas" in row["infover"]
        and row["genre"] in ("m", "f") and row["nombre"] in ("s", "p")
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pad the syll_cv of the synthetic past-participle rows of "
        "resources/LexiqueSynthetic.tsv with one silent '#' per missing orthographic unit (item B46)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to resources/LexiqueSynthetic.tsv (default: dry-run).",
    )
    args = parser.parse_args()

    with open(LEXIQUE_SYNTHETIC_PATH, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\r\n").split("\t")
    syllIdx = header.index("syll_cv")
    orthoSyllIdx = header.index("orthosyll_cv")

    kept = [lines[0]]
    counts: collections.Counter[str] = collections.Counter()
    examples: dict[str, list[str]] = collections.defaultdict(list)
    for line in lines[1:]:
        body = line.rstrip("\r\n")
        fields = body.split("\t")
        row = dict(zip(header, fields))
        if not body.strip() or not isParticipleRow(row):
            kept.append(line)
            continue
        counts["selected"] += 1
        try:
            padded = _padSilentUnits(fields[syllIdx], fields[orthoSyllIdx])
        except ValueError as error:
            counts["error"] += 1
            examples["error"].append(f"  {row['ortho']:<16} {row['lemme']:<16} {error}")
            kept.append(line)
            continue
        if padded == fields[syllIdx]:
            counts["already aligned"] += 1
            kept.append(line)
            continue
        counts["padded"] += 1
        if len(examples["padded"]) < 10:
            examples["padded"].append(
                f"  {row['ortho']:<16} {fields[syllIdx]} -> {padded}   ({fields[orthoSyllIdx]})"
            )
        fields[syllIdx] = padded
        kept.append("\t".join(fields) + line[len(body):])

    print(", ".join(f"{name}: {count}" for name, count in counts.items()))
    for kind, lines_ in examples.items():
        print(f"{kind}:")
        print("\n".join(lines_))

    if counts["padded"] == 0 and counts["error"] == 0:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)
    if args.apply:
        with open(LEXIQUE_SYNTHETIC_PATH, "w", newline="") as f:
            f.writelines(kept)
        print(f"--apply: wrote {LEXIQUE_SYNTHETIC_PATH}")


if __name__ == "__main__":
    main()
