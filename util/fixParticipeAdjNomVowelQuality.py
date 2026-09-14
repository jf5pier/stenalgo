#!/bin/env python
#
# 137 orthos have a past-participle VER row and an ADJ/NOM homograph row
# whose `phon` disagrees purely by the case of one letter (open E vs closed
# e) -- found while regenerating LexiqueMixte.tsv and reviewed with the user
# via a published table (137 rows, one per ortho). Per the user's review:
# for 134 of them the VER row is correct and the ADJ/NOM row is the stale
# one (general rule: participle vowel quality doesn't change when the same
# form is read as an adjective/noun); 3 exceptions (fieffé, fieffée,
# minerai) go the other way and were already fixed by hand in this session.
#
# CAUTION -- this list originally included "ai", "aurai", "serai" (3 more
# of the 137), which turned out NOT to belong here: they're avoir/être's
# genuinely distinct AUX-vs-VER conjugated forms, not a participle/ADJ/NOM
# homograph, and resources/LexiqueInfraCorrespondance.tsv already carries a
# correct, DIFFERENT phono value per cgram for each -- unifying them (as
# this script initially did) orphaned the AUX row's infra entry and broke
# `python lexique.py` (3 "Not found in Lexique383" errors). They were
# reverted by hand and are deliberately excluded from ORTHOS below.
#
# This script fixes the (now 131-word) majority direction: for each ortho below,
# copies the VER row's `phon`/`syll`/`phonrenv` onto every non-VER row of
# the same ortho in resources/Lexique383.tsv (confirmed: once `phon`
# matches, `syll`/`phonrenv` are mechanically derived from `phon`+`ortho`
# and become byte-identical to the VER row's own values -- verified on the
# 3 hand-fixed exceptions before writing this script), and does the
# equivalent for resources/LexiqueMixte.tsv's `syll_cv` where a
# corresponding non-VER row already exists there (`orthosyll_cv` is
# orthographic and untouched). resources/LexiqueInfraCorrespondance.tsv is
# checked but, per a spot-check across several of these orthos (enseigné,
# aimé, blessé), already carries the correct phono/assoc for every cgram --
# so no infra changes are expected; any exception is reported, not silently
# skipped.
#
# Dry-run by default: only reads and reports. --apply writes phon/syll/
# phonrenv (Lexique383.tsv) and syll_cv (LexiqueMixte.tsv) corrections in
# place. Idempotent: a no-op if run again after a successful --apply.
import argparse
import csv

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"

# The 3 already-fixed exceptions (VER was wrong, not the ADJ/NOM row) are
# deliberately excluded from this list.
ORTHOS: set[str] = {
    "abaissé", "abaissée", "abaissées", "abaissés",
    "affairé", "affairée", "affairées", "affairés",
    "aimé", "aimée", "aimées", "aimés",
    "apprêté", "apprêtée", "apprêtées", "apprêtés",
    "arrêté", "arrêtée", "arrêtées", "arrêtés",
    "biaisé", "biaisée",
    "blessé", "blessée", "blessées", "blessés",
    "braisé", "braisée",
    "dressé", "dressée", "dressées", "dressés",
    "démêlés",
    "déterré", "déterrée", "déterrées", "déterrés",
    "emmêlé", "emmêlée", "emmêlées", "emmêlés",
    "empierré", "empierrée",
    "empressé", "empressée", "empressées", "empressés",
    "empêché", "empêchée", "empêchés",
    "encaissé", "encaissée", "encaissées", "encaissés",
    "enchaîné", "enchaînée", "enchaînées", "enchaînés",
    "endetté", "endettée", "endettés",
    "enneigé", "enneigée", "enneigées", "enneigés",
    "enseigné", "enseignée", "enseignés",
    "enterré", "enterrée", "enterrées", "enterrés",
    "entraîné", "entraînée", "entraînées", "entraînés",
    "entêté", "entêtée", "entêtés",
    "fouetté", "fouettés",
    "guêtré",
    "intéressé", "intéressée", "intéressées", "intéressés",
    "libellé",
    "mêlé", "mêlée", "mêlées", "mêlés",
    "peigné", "peignés",
    "pressé", "pressés",
    "prêté", "prêtée", "prêtées", "prêtés",
    "pêché", "pêchés",
    "resserré", "resserrée", "resserrées", "resserrés",
    "rêvé", "rêvée", "rêvées", "rêvés",
    "saignée", "saignées",
    "scellé", "scellée", "scellées", "scellés",
    "traité", "traitée", "traitées", "traités",
    "traînée", "traînées",
    "veillé", "veillée",
    "éclairé", "éclairée", "éclairées", "éclairés",
    "éveillé", "éveillée", "éveillées", "éveillés",
}


def readTsvRows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def applyLexique383(apply: bool) -> tuple[list[str], list[str]]:
    with open(LEXIQUE_383_PATH, newline="", encoding="utf-8") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\n").split("\t")
    idx = {name: header.index(name) for name in
           ("ortho", "phon", "cgram", "syll", "phonrenv")}

    verByOrtho: dict[str, dict[str, str]] = {}
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        if fields[idx["ortho"]] in ORTHOS and fields[idx["cgram"]] == "VER":
            verByOrtho[fields[idx["ortho"]]] = {
                "phon": fields[idx["phon"]],
                "syll": fields[idx["syll"]],
                "phonrenv": fields[idx["phonrenv"]],
            }

    fixed: list[str] = []
    skipped: list[str] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        ortho = fields[idx["ortho"]]
        if ortho not in ORTHOS or fields[idx["cgram"]] == "VER":
            continue
        ver = verByOrtho.get(ortho)
        if ver is None:
            skipped.append(f"{ortho!r} (cgram={fields[idx['cgram']]!r}): no VER sibling found")
            continue
        oldPhon = fields[idx["phon"]]
        if oldPhon == ver["phon"]:
            continue  # already matches
        if oldPhon.lower() != ver["phon"].lower():
            skipped.append(
                f"{ortho!r} (cgram={fields[idx['cgram']]!r}): phon {oldPhon!r} vs "
                f"VER {ver['phon']!r} differ by more than case, not touching"
            )
            continue
        fixed.append(
            f"{ortho!r} cgram={fields[idx['cgram']]!r}: "
            f"phon {oldPhon!r} -> {ver['phon']!r}"
        )
        if apply:
            fields[idx["phon"]] = ver["phon"]
            fields[idx["syll"]] = ver["syll"]
            fields[idx["phonrenv"]] = ver["phonrenv"]
            lines[i] = "\t".join(fields) + "\n"

    if apply and fixed:
        with open(LEXIQUE_383_PATH, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return fixed, skipped


def applyLexiqueMixte(apply: bool) -> tuple[list[str], list[str]]:
    with open(LEXIQUE_MIXTE_PATH, newline="", encoding="utf-8") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\n").split("\t")
    idx = {name: header.index(name) for name in
           ("ortho", "phon", "cgram", "syll_cv")}

    verByOrtho: dict[str, dict[str, str]] = {}
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        if fields[idx["ortho"]] in ORTHOS and fields[idx["cgram"]] == "VER":
            verByOrtho[fields[idx["ortho"]]] = {
                "phon": fields[idx["phon"]],
                "syll_cv": fields[idx["syll_cv"]],
            }

    fixed: list[str] = []
    skipped: list[str] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        ortho = fields[idx["ortho"]]
        if ortho not in ORTHOS or fields[idx["cgram"]] == "VER":
            continue
        ver = verByOrtho.get(ortho)
        if ver is None:
            continue  # no VER row in LexiqueMixte.tsv for this ortho -- nothing to reconcile
        oldPhon = fields[idx["phon"]]
        if oldPhon == ver["phon"]:
            continue
        if oldPhon.lower() != ver["phon"].lower():
            skipped.append(
                f"{ortho!r} cgram={fields[idx['cgram']]!r}: phon {oldPhon!r} vs "
                f"VER {ver['phon']!r} differ by more than case, not touching"
            )
            continue
        fixed.append(
            f"{ortho!r} cgram={fields[idx['cgram']]!r}: "
            f"phon {oldPhon!r} -> {ver['phon']!r}"
        )
        if apply:
            fields[idx["phon"]] = ver["phon"]
            fields[idx["syll_cv"]] = ver["syll_cv"]
            lines[i] = "\t".join(fields) + ending

    if apply and fixed:
        with open(LEXIQUE_MIXTE_PATH, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return fixed, skipped


def checkLexiqueInfra() -> list[str]:
    """Report-only: confirms infra already agrees for every cgram (expected)."""
    rows = readTsvRows(LEXIQUE_INFRA_PATH)
    byOrtho: dict[str, set[str]] = {}
    for row in rows:
        if row["item"] in ORTHOS:
            byOrtho.setdefault(row["item"], set()).add(row["phono"])
    problems = []
    for ortho, phonos in byOrtho.items():
        if len(phonos) > 1:
            problems.append(f"{ortho!r}: multiple phono values in infra {sorted(phonos)!r}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix the 134-word majority-direction e/E vowel-quality "
        "mismatch between a past-participle VER row and its ADJ/NOM "
        "homograph, per the user's per-word review."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to Lexique383.tsv and LexiqueMixte.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    fixed383, skipped383 = applyLexique383(args.apply)
    print(f"=== {LEXIQUE_383_PATH} ===")
    for f in fixed383:
        print(f"  FIX: {f}")
    for s in skipped383:
        print(f"  SKIP: {s}")
    print(f"Fixed: {len(fixed383)}, skipped: {len(skipped383)}\n")

    fixedMixte, skippedMixte = applyLexiqueMixte(args.apply)
    print(f"=== {LEXIQUE_MIXTE_PATH} ===")
    for f in fixedMixte:
        print(f"  FIX: {f}")
    for s in skippedMixte:
        print(f"  SKIP: {s}")
    print(f"Fixed: {len(fixedMixte)}, skipped: {len(skippedMixte)}\n")

    infraProblems = checkLexiqueInfra()
    print(f"=== {LEXIQUE_INFRA_PATH} (check-only, never written) ===")
    if infraProblems:
        for p in infraProblems:
            print(f"  UNEXPECTED: {p}")
    else:
        print("  OK: every affected ortho already agrees on one phono value.")

    if args.apply:
        print(f"\n--apply: updated {LEXIQUE_383_PATH} and {LEXIQUE_MIXTE_PATH}")


if __name__ == "__main__":
    main()
