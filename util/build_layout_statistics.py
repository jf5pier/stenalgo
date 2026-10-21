"""Layout statistics for the keyboard layout solve (S4), rebuilt from a phonetic theory (docs/PHONOLOGY_REWRITE_PLAN.md PRP11).

Run: python -m util.build_layout_statistics [--rewrite] [--output PATH]   (from the repo root; ~1.5 min)
Reads PhoneticTheory.pickle and starboard3h.json, builds the phoneme/biphoneme/multiphoneme statistics and the three ambiguity tables from the
theory's words (src/layoutstatistics.py), and writes ONE self-contained file for `python -m util.optimize_keyboard --statistics PATH`
(a remote machine needs that file, src/, the pinned ortools and the seed layout, nothing else).
Without --rewrite the file reproduces today's statistics (util.check_layout_statistics proves it). With --rewrite the phonology overrides
(resources/phonologyOverrides.tsv) are applied first and the overridden spellings (je te se le ce de me ne que) are weighed with their
forced phonology; the rest of the top-200 stays at weight 0.
Never touches Dictionary.pickle: the theory build reuses that file unchecked, and the rewrite is never pickled (PRB12).
Default output LayoutStatistics.pickle (gitignored cache, rebuilt on demand).
"""
import argparse
import hashlib
import os
import pickle
import time

from src.grammar import Syllable
from src.keyboard import Starboard
from src.strokes import Strokes
from src.layoutstatistics import (
    ambiguityTables, buildSyllableStatistics, layoutInput, loadFrequentWords, saveLayoutStatistics,
)
from src.phonologyrewrite import OVERRIDES_PATH
from src.word import Word

THEORY_PICKLE = "PhoneticTheory.pickle"
SEED_PATH = "starboard3h.json"
DEFAULT_OUTPUT = "LayoutStatistics.pickle"
INPUT_FILES = ("resources/LexiqueMixte.tsv", "resources/LexiqueSynthetic.tsv", SEED_PATH, OVERRIDES_PATH, "resources/top500_film.txt")


def md5(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as ffile:
        return hashlib.md5(ffile.read()).hexdigest()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m util.build_layout_statistics", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rewrite", action="store_true", help="apply the phonology overrides first (default: the theory as built)")
    parser.add_argument("--output", metavar="PATH", default=DEFAULT_OUTPUT, help=f"default {DEFAULT_OUTPUT}")
    args = parser.parse_args(argv)

    keyboard = Starboard.fromJSONFile(SEED_PATH)
    if keyboard is None:
        raise SystemExit(f"{SEED_PATH} not found.")
    if not os.path.exists(THEORY_PICKLE):
        raise SystemExit(f"{THEORY_PICKLE} not found: run `python -m util.build_phonetic_theory` first.")
    with open(THEORY_PICKLE, "rb") as pfile:
        theory: dict[Strokes, list[Word]] = pickle.load(pfile)

    words, excluded = layoutInput(theory, loadFrequentWords(), keyboard, args.rewrite)
    collection = buildSyllableStatistics(words, excluded)
    Syllable.optimizeBiphonemeOrder()
    tables = ambiguityTables(collection)
    meta = {"rewrite": args.rewrite, "words": len(words), "excluded": sorted(excluded), "built": time.strftime("%Y-%m-%d %H:%M:%S"),
            "inputs": {path: md5(path) for path in INPUT_FILES}}
    saveLayoutStatistics(args.output, tables, meta)
    print(f"\nWrote the layout statistics ({len(words)} words, rewrite {'on' if args.rewrite else 'off'}, "
          f"{len(excluded)} spellings at weight 0) to {args.output}.")


if __name__ == "__main__":
    main()
