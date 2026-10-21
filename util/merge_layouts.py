"""Combines the per-part layouts of a remote solve (one `util.optimize_keyboard --parts PART --output FILE` process per part) into one layout.

Run: python -m util.merge_layouts --output PATH onset=FILE [nucleus=FILE] [coda=FILE] [--seed starboard3h.json]
A part not given keeps the seed's strokes. Each FILE (a solver output or an incumbent_<part>.json) must hold exactly the strokes of its part: only keys of
that part, every phoneme of the part assigned once. Refuses to overwrite the seed. Exit 1 on a layout that fails these checks.
"""
import argparse
import os

from src.grammar import Phoneme
from src.keyboard import Starboard
from src.strokes import Stroke

SEED_PATH = "starboard3h.json"
PHONEMES_OF_PART = {"onset": Phoneme.consonantPhonemes, "nucleus": Phoneme.nucleusPhonemes, "coda": Phoneme.consonantPhonemes}


def checkPart(part: str, strokes: dict[Stroke, list[str]], board: Starboard, label: str) -> list[str]:
    """The problems of a part layout, empty when it is sound."""
    problems: list[str] = []
    keys = set(board.keyIDinSyllabicPart[part])
    for stroke in strokes:
        if not stroke or not set(stroke) <= keys:
            problems.append(f"{label}: stroke {stroke} is not made of {part} keys")
    assigned = sorted(phoneme for phonemes in strokes.values() for phoneme in phonemes)
    if assigned != sorted(PHONEMES_OF_PART[part]):
        missing = set(PHONEMES_OF_PART[part]) - set(assigned)
        extra = [p for p in assigned if assigned.count(p) > 1 or p not in PHONEMES_OF_PART[part]]
        problems.append(f"{label}: {part} phonemes are not each assigned once (missing {sorted(missing)}, repeated or foreign {sorted(set(extra))})")
    return problems


def merge(seed: Starboard, partFiles: dict[str, str]) -> Starboard:
    """The seed with the strokes of each given part replaced by the part file's. Raises ValueError listing every problem found."""
    merged = seed
    replacement: dict[str, dict[Stroke, list[str]]] = {}
    problems: list[str] = []
    for part, path in partFiles.items():
        board = Starboard.fromJSONFile(path)
        if board is None:
            problems.append(f"{path}: not found")
            continue
        replacement[part] = board.phonemesAssignedToStroke
        problems += checkPart(part, board.phonemesAssignedToStroke, merged, f"{part} ({path})")
    if problems:
        raise ValueError("\n".join(problems))
    kept = {stroke: phonemes for stroke, phonemes in merged.phonemesAssignedToStroke.items()
            if not any(set(stroke) <= set(merged.keyIDinSyllabicPart[part]) for part in replacement)}
    merged.clearLayout()
    for stroke, phonemes in kept.items():
        for phoneme in phonemes:
            merged.addToLayout(stroke, phoneme)
    for strokes in replacement.values():
        for stroke, phonemes in strokes.items():
            for phoneme in phonemes:
                merged.addToLayout(stroke, phoneme)
    return merged


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m util.merge_layouts", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("parts", nargs="+", metavar="PART=FILE", help="onset=FILE nucleus=FILE coda=FILE (any subset)")
    parser.add_argument("--seed", default=SEED_PATH, help=f"the layout the missing parts come from (default {SEED_PATH})")
    parser.add_argument("--output", required=True, metavar="PATH")
    args = parser.parse_args(argv)

    partFiles: dict[str, str] = {}
    for item in args.parts:
        part, _, path = item.partition("=")
        if part not in PHONEMES_OF_PART or not path:
            raise SystemExit(f"expected PART=FILE with PART in {sorted(PHONEMES_OF_PART)}, got {item!r}")
        partFiles[part] = path
    if os.path.abspath(args.output) == os.path.abspath(SEED_PATH):
        raise SystemExit(f"refusing to overwrite {SEED_PATH}: write the merged layout elsewhere and adopt it deliberately.")
    seed = Starboard.fromJSONFile(args.seed)
    if seed is None:
        raise SystemExit(f"{args.seed} not found.")
    try:
        merged = merge(seed, partFiles)
    except ValueError as error:
        print(error)
        raise SystemExit(1)
    merged.toJSONFile(args.output)
    print(f"Wrote the merged layout ({', '.join(partFiles)} from the given files, the rest from {args.seed}) to {args.output}.")


if __name__ == "__main__":
    main()
