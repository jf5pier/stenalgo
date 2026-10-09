#!/usr/bin/env python
# coding: utf-8
"""
Check lexicon files (LexiqueMixte.tsv and LexiqueSynthetic.tsv) for data integrity.

Runs checks on each row:
1. columns: row has the header's number of fields
2. units: syll_cv and orthosyll_cv split on | and _ give same number of units, no empty units; a repeat unit `=`
   (src/orthounits.py) only on the orthosyll_cv side, right after a letter unit of its own, opposite a sounded unit
3. sounded: joining non-# units from syll_cv gives exactly phon
4. infover (VER only): non-empty, ends with ;, valid tags
5. participle (VER with par:pas): genre m/f, nombre s/p, or has other tags
6. excluded: no VER tag starts with sub:imp
7. duplicateIdentity (Synthetic only): no row matches a Mixte row's identity
8. features (smoke): construct Word from first 2000 rows, call getFeatures()
"""

import csv
import re
import sys
from argparse import ArgumentParser
from collections import Counter
from typing import Any

from src.orthounits import REPEAT, SILENT
from src.word import Word, GramCat


def count_units(s: str) -> int:
    """Count units in a syllabic string split on | and _."""
    if not s:
        return 0
    units = s.replace("|", "_").split("_")
    return len([u for u in units if u])


def check_units(syll_cv: str, orthosyll_cv: str) -> bool:
    """Check that syll_cv and orthosyll_cv have same number of units, no empty units."""
    # Split on both | and _ and check that no unit is empty
    syll_units = syll_cv.replace("|", "_").split("_")
    ortho_units = orthosyll_cv.replace("|", "_").split("_")

    # Check for empty units (consecutive delimiters)
    if "" in syll_units or "" in ortho_units:
        return False

    # Check same count and non-empty
    if len(syll_units) != len(ortho_units) or not syll_units:
        return False
    if REPEAT in syll_units:
        return False
    for at, unit in enumerate(ortho_units):
        if unit == REPEAT and (at == 0 or ortho_units[at - 1] == REPEAT or syll_units[at - 1] == SILENT or syll_units[at] == SILENT):
            return False
    return True


def sounded_from_syllcv(syll_cv: str) -> str:
    """Join all non-# units from syll_cv."""
    units = [u for u in syll_cv.replace("|", "_").split("_") if u and u != "#"]
    return "".join(units)


def check_sounded(syll_cv: str, phon: str) -> bool:
    """Check that sounded units from syll_cv equal phon."""
    return sounded_from_syllcv(syll_cv) == phon


def check_infover_tag(tag: str) -> bool:
    """Check if a single infover tag is valid."""
    if tag == "inf":
        return True
    if tag in ("par:pre", "par:pas"):
        return True
    # ind:(pre|imp|pas|fut):[123][sp]
    # cnd:pre:[123][sp]
    # sub:pre:[123][sp]
    # imp:pre:[123][sp]
    pattern = r"^(ind:(pre|imp|pas|fut)|cnd:pre|sub:pre|imp:pre):[123][sp]$"
    return bool(re.match(pattern, tag))


def check_infover(infover: str | None, cgram: str) -> tuple[bool, str]:
    """
    Check infover field.
    Returns (is_valid, msg) where msg explains failure if not valid.
    Only check for VER.
    """
    if cgram != "VER":
        return (True, "")

    if not infover:
        return (False, "VER infover is empty")

    if not infover.endswith(";"):
        return (False, "VER infover does not end with ;")

    tags = [t for t in infover.split(";") if t]
    for tag in tags:
        if not check_infover_tag(tag):
            return (False, f"Invalid tag: {tag}")

    return (True, "")


def check_excluded(infover: str | None, cgram: str) -> tuple[bool, str]:
    """Check that no VER tag starts with sub:imp."""
    if cgram != "VER" or not infover:
        return (True, "")

    tags = [t for t in infover.split(";") if t]
    for tag in tags:
        if tag.startswith("sub:imp"):
            return (False, f"Found sub:imp tag: {tag}")

    return (True, "")


def check_participle(
    infover: str | None, genre: str | None, nombre: str | None, cgram: str
) -> tuple[bool, str]:
    """
    Check participle rows.
    Returns (is_valid, msg).
    Warning if check fails (False + msg), but report as warning not failure.
    """
    if cgram != "VER" or not infover or "par:pas" not in infover:
        return (True, "")

    # Check if there are other tags
    tags = [t for t in infover.split(";") if t]
    has_other_tags = len(tags) > 1

    if has_other_tags:
        return (True, "")  # Skip if has other tags

    # Must have genre m/f and nombre s/p
    if genre not in ("m", "f"):
        return (False, f"Participle with invalid genre: {genre}")

    if nombre not in ("s", "p"):
        return (False, f"Participle with invalid nombre: {nombre}")

    return (True, "")


def check_columns(row: dict[str, str], expected_count: int) -> bool:
    """Check that row has expected number of columns."""
    return len(row) == expected_count


def construct_word(row: dict[str, str]) -> Word:
    """Construct a Word from a lexicon row, mimicking dictionary.py's readCorpus."""
    genre = row["genre"] if row["genre"] != "" else None
    nombre = row["nombre"] if row["nombre"] != "" else None
    infover = row["infover"] if row["infover"] != "" else None

    word = Word(
        ortho=row["ortho"],
        phonology=row["phon"],
        lemme=row["lemme"],
        gramCat=GramCat[row["cgram"]],
        orthoGramCat=[GramCat[gc] for gc in row["cgramortho"].split(",")],
        gender=genre,
        number=nombre,
        infoVerb=infover,
        rawSyllCV=row["syll_cv"],
        rawOrthosyllCV=row["orthosyll_cv"],
        frequencyBook=float(row["freqlivres"]),
        frequencyFilm=float(row["freqfilms2"]),
    )
    return word


def check_file(
    path: str, max_examples: int = 5, is_synthetic: bool = False
) -> dict[str, Any]:
    """
    Check a lexicon file.
    Returns dict with check results.
    """
    results: dict[str, Any] = {
        "columns": Counter(),
        "units": Counter(),
        "sounded": Counter(),
        "infover": Counter(),
        "participle": Counter(),
        "excluded": Counter(),
        "duplicateIdentity": Counter() if is_synthetic else None,
        "features": Counter(),
        "examples": {
            "columns": [],
            "units": [],
            "sounded": [],
            "infover": [],
            "participle": [],
            "excluded": [],
            "duplicateIdentity": [] if is_synthetic else None,
            "features": [],
        },
    }

    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print(f"Error: No fieldnames in {path}")
            return results

        expected_count = len(fieldnames)
        rows = list(reader)

        for row_idx, row in enumerate(rows):
            # Check 1: columns
            if not check_columns(row, expected_count):
                results["columns"]["FAIL"] += 1
                if len(results["examples"]["columns"]) < max_examples:
                    results["examples"]["columns"].append(
                        (row_idx, f"Expected {expected_count}, got {len(row)}")
                    )

            # Check 2: units
            if not check_units(row["syll_cv"], row["orthosyll_cv"]):
                results["units"]["FAIL"] += 1
                if len(results["examples"]["units"]) < max_examples:
                    results["examples"]["units"].append(
                        (row_idx, row["ortho"], "Unit mismatch or empty units")
                    )

            # Check 3: sounded
            if not check_sounded(row["syll_cv"], row["phon"]):
                results["sounded"]["FAIL"] += 1
                if len(results["examples"]["sounded"]) < max_examples:
                    expected = sounded_from_syllcv(row["syll_cv"])
                    results["examples"]["sounded"].append(
                        (row_idx, row["ortho"], f"Expected {expected}, got {row['phon']}")
                    )

            # Check 4: infover
            valid, msg = check_infover(row["infover"] or None, row["cgram"])
            if not valid:
                results["infover"]["FAIL"] += 1
                if len(results["examples"]["infover"]) < max_examples:
                    results["examples"]["infover"].append((row_idx, row["ortho"], msg))

            # Check 5: participle (warning)
            valid, msg = check_participle(
                row["infover"] or None,
                row["genre"] or None,
                row["nombre"] or None,
                row["cgram"],
            )
            if not valid:
                results["participle"]["WARN"] += 1
                if len(results["examples"]["participle"]) < max_examples:
                    results["examples"]["participle"].append((row_idx, row["ortho"], msg))

            # Check 6: excluded
            valid, msg = check_excluded(row["infover"] or None, row["cgram"])
            if not valid:
                results["excluded"]["FAIL"] += 1
                if len(results["examples"]["excluded"]) < max_examples:
                    results["examples"]["excluded"].append((row_idx, row["ortho"], msg))

            # Check 8: features (first 2000 rows only)
            if row_idx < 2000:
                try:
                    word = construct_word(row)
                    features = word.getFeatures()
                    if not features:
                        results["features"]["FAIL"] += 1
                        if len(results["examples"]["features"]) < max_examples:
                            results["examples"]["features"].append(
                                (row_idx, row["ortho"], "No features returned")
                            )
                    else:
                        results["features"]["OK"] += 1
                except Exception as e:
                    results["features"]["FAIL"] += 1
                    if len(results["examples"]["features"]) < max_examples:
                        results["examples"]["features"].append(
                            (row_idx, row["ortho"], str(e))
                        )

        # Check 7: duplicateIdentity (Synthetic only)
        if is_synthetic:
            for row in rows:
                identity = (
                    row["ortho"],
                    row["phon"],
                    row["lemme"],
                    row["cgram"],
                    row["genre"] or None,
                    row["nombre"] or None,
                )
                # Store for later comparison
                if not hasattr(results, "synthetic_identities"):
                    results["synthetic_identities"] = set()  # type: ignore
                results["synthetic_identities"].add(identity)  # type: ignore

    results["total_rows"] = len(rows)
    return results


def check_duplicate_identity(
    mixte_results: dict[str, Any], synthetic_results: dict[str, Any], max_examples: int
) -> tuple[int, list[tuple[int, str, str]]]:
    """
    Check that no Synthetic row has same identity as a Mixte row.
    Returns (warning_count, examples).
    Note: This is a warning, not a failure (Dictionary loading merges these).
    """
    # We need to re-read to get row indices
    mixte_identities: dict[tuple[str, str, str, str, str | None, str | None], int] = {}

    with open("resources/LexiqueMixte.tsv", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            identity = (
                row["ortho"],
                row["phon"],
                row["lemme"],
                row["cgram"],
                row["genre"] or None,
                row["nombre"] or None,
            )
            mixte_identities[identity] = 1

    warnings = 0
    examples: list[tuple[int, str, str]] = []

    with open("resources/LexiqueSynthetic.tsv", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        for row_idx, row in enumerate(reader):
            identity = (
                row["ortho"],
                row["phon"],
                row["lemme"],
                row["cgram"],
                row["genre"] or None,
                row["nombre"] or None,
            )
            if identity in mixte_identities:
                warnings += 1
                if len(examples) < max_examples:
                    examples.append(
                        (row_idx, row["ortho"], f"Duplicate of Mixte identity")
                    )

    return (warnings, examples)


def main() -> int:
    """Main entry point."""
    parser = ArgumentParser(
        description="Check lexicon files for data integrity"
    )
    parser.add_argument(
        "--mixte",
        default="resources/LexiqueMixte.tsv",
        help="Path to LexiqueMixte.tsv",
    )
    parser.add_argument(
        "--synthetic",
        default="resources/LexiqueSynthetic.tsv",
        help="Path to LexiqueSynthetic.tsv",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=5,
        help="Max examples per check (default 5)",
    )
    args = parser.parse_args()

    max_ex = args.max_examples

    print("=" * 80)
    print("LEXICON INTEGRITY CHECK")
    print("=" * 80)

    # Check Mixte
    print(f"\nChecking {args.mixte}...")
    mixte_results = check_file(args.mixte, max_ex, is_synthetic=False)

    # Check Synthetic
    print(f"Checking {args.synthetic}...")
    synthetic_results = check_file(args.synthetic, max_ex, is_synthetic=True)

    # Check duplicateIdentity
    dup_failures, dup_examples = check_duplicate_identity(
        mixte_results, synthetic_results, max_ex
    )

    # Print summary table
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    checks = [
        "columns",
        "units",
        "sounded",
        "infover",
        "participle",
        "excluded",
        "duplicateIdentity",
        "features",
    ]

    header = f"{'Check':<20} {'Mixte':<15} {'Synthetic':<15}"
    print(header)
    print("-" * 50)

    any_failures = False

    for check in checks:
        if check == "duplicateIdentity":
            mixte_count = 0
            synthetic_count = dup_failures
        else:
            mixte_count = (
                mixte_results[check]["FAIL"]
                if check in mixte_results and mixte_results[check] and "FAIL" in mixte_results[check]
                else 0
            )
            synthetic_count = (
                synthetic_results[check]["FAIL"]
                if check in synthetic_results and synthetic_results[check] and "FAIL" in synthetic_results[check]
                else 0
            )

        if check == "participle" or check == "duplicateIdentity":
            # Print as warning
            if check == "participle":
                mixte_warn = (
                    mixte_results[check]["WARN"]
                    if "WARN" in mixte_results[check]
                    else 0
                )
                synthetic_warn = (
                    synthetic_results[check]["WARN"]
                    if "WARN" in synthetic_results[check]
                    else 0
                )
                print(f"{check:<20} {mixte_warn:<15} (warn) {synthetic_warn:<15} (warn)")
            else:  # duplicateIdentity
                print(f"{check:<20} {0:<15} (warn) {synthetic_count:<15} (warn)")
        else:
            print(f"{check:<20} {mixte_count:<15} {synthetic_count:<15}")
            if mixte_count > 0 or synthetic_count > 0:
                any_failures = True

    # Print examples
    print("\n" + "=" * 80)
    print("EXAMPLES")
    print("=" * 80)

    for check in checks:
        if check == "duplicateIdentity":
            if dup_examples:
                print(f"\n{check}:")
                for example in dup_examples:
                    print(f"  Row {example[0]}: {example[1]} - {example[2]}")
        else:
            if (
                check in mixte_results["examples"]
                and mixte_results["examples"][check]
            ):
                print(f"\n{check} (Mixte):")
                for example in mixte_results["examples"][check]:
                    print(f"  Row {example[0]}: {example[1]} - {example[2]}")

            if (
                check in synthetic_results["examples"]
                and synthetic_results["examples"][check]
            ):
                print(f"\n{check} (Synthetic):")
                for example in synthetic_results["examples"][check]:
                    print(f"  Row {example[0]}: {example[1]} - {example[2]}")

    print("\n" + "=" * 80)
    print("TOTAL ROWS")
    print("=" * 80)
    print(f"Mixte:     {mixte_results['total_rows']}")
    print(f"Synthetic: {synthetic_results['total_rows']}")

    return 1 if any_failures else 0


if __name__ == "__main__":
    sys.exit(main())
