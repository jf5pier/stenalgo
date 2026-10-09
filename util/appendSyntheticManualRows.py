#!/bin/env python
"""
Synthetic Lexicon Building (S2.4): append the hand-derived rows of resources/syntheticManualRows.tsv
(same columns as LexiqueSynthetic.tsv; the 21 ass:eoir / r:asseoir dual-form gaps that no donor could
fill, derived with the user in util/fixAsseoirDualFormGapsManual.py) to resources/LexiqueSynthetic.tsv.

This keeps the Synthetic file a function of committed inputs: the rows live in a data file, not in a
hand-run script's source. A row is appended unless the Synthetic file already holds one with the same
(ortho, lemme, infover), so the step is idempotent. The rows' spelling-variant drops are handled by the
prune step of util.build_synthetic_lexicon.

Dry-run by default; --apply appends. Run: python -m util.appendSyntheticManualRows [--apply]
"""
import argparse
import os

MANUAL_ROWS_PATH = "resources/syntheticManualRows.tsv"
SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
KEY_COLUMNS = (0, 2, 7)  # ortho, lemme, infover


def readDataLines(path: str) -> tuple[str, list[str]]:
    with open(path, encoding="utf-8", newline="") as f:
        lines = [line.rstrip("\r") for line in f.read().split("\n")]  # the Synthetic file mixes CRLF and LF rows
    header, body = lines[0], [line for line in lines[1:] if line.strip()]
    return header, body


def rowKey(line: str) -> tuple[str, ...]:
    fields = line.split("\t")
    return tuple(fields[i] for i in KEY_COLUMNS)


def missingRows(manualLines: list[str], syntheticLines: list[str]) -> list[str]:
    """The manual rows whose (ortho, lemme, infover) the Synthetic file does not hold yet, in file order."""
    present = {rowKey(line) for line in syntheticLines}
    return [line for line in manualLines if rowKey(line) not in present]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Append the missing rows (default: dry-run).")
    args = parser.parse_args()
    manualHeader, manualLines = readDataLines(MANUAL_ROWS_PATH)
    syntheticHeader, syntheticLines = readDataLines(SYNTHETIC_PATH)
    assert manualHeader == syntheticHeader, "resources/syntheticManualRows.tsv must have the Synthetic header"
    toAppend = missingRows(manualLines, syntheticLines)
    for line in toAppend:
        print("  +", line.split("\t")[0], line.split("\t")[2], line.split("\t")[7])
    if args.apply and toAppend:
        with open(SYNTHETIC_PATH, "a", encoding="utf-8", newline="") as f:
            f.write("".join(line + "\n" for line in toAppend))
    print(f"--apply: appended {len(toAppend)} rows to {SYNTHETIC_PATH}" if args.apply
          else f"dry-run: {len(toAppend)} rows would be appended (pass --apply)")


if __name__ == "__main__":
    main()
