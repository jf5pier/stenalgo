#!/bin/env python
#
# Corrects malformed spliced rows in resources/LexiqueSynthetic.tsv: the conjugated
# forms that src/verbparadigm.py's generateMissingConjugatedForm built before it
# repaired its fixed-length cuts. Three defects survive in stored rows: an empty
# unit in syll_cv (clouerions "k_l_u#|..." cut for a silent e, halées "_a|l_e"), a
# fused "X#" unit where attested rows write X + a silent "#" unit, and a phon that
# no longer matches the sounded units (clouerions "kluj§" for "kluRj§"; phon is then
# rewritten to the sounded join when rewriteSplicePhon deems it safe).
#
# Rule per row: repairSpliceUnits on syll_cv (and on orthosyll_cv if it has the
# same defects); if isWellFormedSplice(phon, syll_cv) and both fields then have the
# same unit count, rewrite them; otherwise the row is DELETED (the Synthetic
# Lexicon Building (S2) appenders refill it, or not, with the fixed generator).
# Rows already passing the guard are untouched.
#
# Dry-run by default. --apply rewrites the file keeping every untouched byte and
# each row's own line ending. Idempotent. Rerun S2 afterwards, with the pickles deleted.
import argparse
import collections
import sys

from src.verbparadigm import isWellFormedSplice, reinsertLostNasalUnit, repairSpliceUnits, rewriteSplicePhon, _unitsAndBoundaries

LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def _nUnits(breakdown: str) -> int:
    return len(_unitsAndBoundaries(breakdown)[0])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repair or delete the malformed spliced rows of resources/LexiqueSynthetic.tsv."
    )
    parser.add_argument("--apply", action="store_true",
                        help="Write the result back (default: dry-run).")
    args = parser.parse_args()

    with open(LEXIQUE_SYNTHETIC_PATH, newline="", encoding="utf-8") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\r\n").split("\t")
    idx = {name: header.index(name) for name in header}
    with open(LEXIQUE_MIXTE_PATH, newline="", encoding="utf-8") as f:
        mixteHeader = f.readline().rstrip("\r\n").split("\t")
        oI, lI, vI = (mixteHeader.index(n) for n in ("ortho", "lemme", "infover"))
        mixte = set()
        for line in f:
            p = line.rstrip("\r\n").split("\t")
            if len(p) > vI:
                mixte.add((p[oI], p[lI], p[vI]))

    kept = [lines[0]]
    counts: collections.Counter[str] = collections.Counter()
    deleted: dict[str, list[str]] = collections.defaultdict(list)
    surprising: list[str] = []
    rewrites: list[str] = []
    reinserted: list[str] = []
    inMixte = 0
    for line in lines[1:]:
        body = line.rstrip("\r\n")
        fields = body.split("\t")
        if not body.strip() or len(fields) < len(header):
            kept.append(line)
            counts["unchanged"] += 1
            continue
        phon, syll, ortho = fields[idx["phon"]], fields[idx["syll_cv"]], fields[idx["orthosyll_cv"]]
        if syll and isWellFormedSplice(phon, syll):
            kept.append(line)
            counts["unchanged"] += 1
            continue
        newSyll = repairSpliceUnits(syll) if syll else syll
        newOrtho = repairSpliceUnits(ortho) if ortho else ortho
        if newOrtho != ortho:
            counts["orthosyll repaired too"] += 1
        if syll and isWellFormedSplice(phon, newSyll) and _nUnits(newSyll) == _nUnits(newOrtho):
            counts["repaired"] += 1
            fields[idx["syll_cv"]], fields[idx["orthosyll_cv"]] = newSyll, newOrtho
            kept.append("\t".join(fields) + line[len(body):])
            continue
        if syll and (fixed := reinsertLostNasalUnit(phon, newSyll, newOrtho)) is not None:
            counts["repaired"] += 1
            counts["nasal unit reinserted"] += 1
            reinserted.append(f"{fields[idx['ortho']]} ({fields[idx['lemme']]}): {syll} {ortho} -> {fixed[0]} {fixed[1]}")
            fields[idx["syll_cv"]], fields[idx["orthosyll_cv"]] = fixed
            kept.append("\t".join(fields) + line[len(body):])
            continue
        if syll and _nUnits(newSyll) == _nUnits(newOrtho) and (newPhon := rewriteSplicePhon(phon, newSyll)) is not None:
            counts["repaired"] += 1
            counts["phon rewritten"] += 1
            rewrites.append(f"{fields[idx['ortho']]} ({fields[idx['lemme']]}): {phon} -> {newPhon}   {newSyll}")
            fields[idx["phon"]], fields[idx["syll_cv"]], fields[idx["orthosyll_cv"]] = newPhon, newSyll, newOrtho
            kept.append("\t".join(fields) + line[len(body):])
            continue
        if syll and isWellFormedSplice(phon, newSyll):
            surprising.append(f"{fields[idx['ortho']]} {newSyll} ({_nUnits(newSyll)}) vs {newOrtho} ({_nUnits(newOrtho)})")
        counts["deleted"] += 1
        key = (fields[idx["ortho"]], fields[idx["lemme"]], fields[idx["infover"]])
        flag = key in mixte
        inMixte += flag
        deleted[fields[idx["lemme"]]].append(
            f"{fields[idx['ortho']]} {phon} {syll} {ortho}" + (" [IN MIXTE]" if flag else ""))

    print(", ".join(f"{k}: {v}" for k, v in counts.items()), f"| deleted also in LexiqueMixte: {inMixte}")
    print(f"Phon rewrites: {len(rewrites)}")
    for r in (rewrites if len(rewrites) < 80 else rewrites[:15]):
        print("  " + r)
    print(f"Nasal unit reinserted: {len(reinserted)}")
    for r in reinserted[:8]:
        print("  " + r)
    print(f"Deleted lemmas: {len(deleted)}")
    for lemme, rows in sorted(deleted.items(), key=lambda kv: -len(kv[1]))[:30]:
        print(f"  {lemme:<14} {len(rows):>3}  {rows[0]}")
    print(f"Unit-count mismatches after repair (deleted): {len(surprising)}")
    for s in surprising[:10]:
        print("  " + s)

    if args.apply:
        with open(LEXIQUE_SYNTHETIC_PATH, "w", newline="", encoding="utf-8") as f:
            f.writelines(kept)
        print(f"--apply: wrote {LEXIQUE_SYNTHETIC_PATH}")
    elif counts["repaired"] + counts["deleted"] == 0:
        print("Nothing found to correct.", file=sys.stderr)


if __name__ == "__main__":
    main()
