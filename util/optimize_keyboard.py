"""
Keyboard Layout Optimization (S4) as a command: the CP-SAT phoneme-to-key
layout solve, runnable without editing code.

Run: python -m util.optimize_keyboard [--output PATH]   (from the repo root)
Seeds from starboard3h.json (the solver uses the committed layout only as CP-SAT
hints, then clears and refills it), optimizes onset/nucleus/coda against
dictionary.syllabicPartAmbiguity, and writes the solved Starboard via toJSONFile.
Default output starboard3h_optimized.json -- the committed seed is NEVER
overwritten silently; pass `--output starboard3h.json` to do it deliberately
(a loud warning is printed).

Rare and costly: ~90 s per syllabic part (the solver's own SOLVER_TIME constant)
plus model building. Requires Dictionary.pickle (or the lexicons, for an
in-memory build that is never persisted) and starboard3h.json.

After adopting a new layout: rm -f Dictionary.pickle PhoneticTheory.pickle and
`python -m util.build_phonetic_theory` (the phonetic theory depends on the
layout; every exporter recomputes the disambiguated theory on its next run).
Exit codes: 0 wrote the layout; 1 seed missing or the solver produced no layout.
"""
import argparse
import os
import sys

from src.cpsatsolver import optimizeKeyboard
from src.keyboard import Starboard
from util._theoryio import loadDictionary

SEED_PATH = "starboard3h.json"
DEFAULT_OUTPUT = "starboard3h_optimized.json"


def parseArgs(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m util.optimize_keyboard",
        description="Keyboard Layout Optimization (S4): the CP-SAT layout solve, seeded from "
                    f"{SEED_PATH}.")
    parser.add_argument("--output", metavar="PATH", default=DEFAULT_OUTPUT,
                        help=f"where to write the solved layout (default: {DEFAULT_OUTPUT}; "
                             f"{SEED_PATH} is overwritten only if passed explicitly)")
    return parser.parse_args(argv)


def _buildDictionaryInMemory():  # type: ignore[no-untyped-def]
    # src/ambiguitychecker.py's __main__ pattern: build without persisting, so this
    # command never silently refreshes the pickle cache.
    from src.grammar import Syllable
    from dictionary import Dictionary
    print("Dictionary.pickle absent -- building the Dictionary in memory (not persisted).")
    dictionary = Dictionary()
    dictionary.analyseSyllabification()
    Syllable.optimizeBiphonemeOrder()
    dictionary.analyseAmbiguities()
    return dictionary


def main(argv: list[str] | None = None) -> None:
    args = parseArgs(argv)
    dictionary = loadDictionary() if os.path.exists("Dictionary.pickle") else _buildDictionaryInMemory()

    starboard = Starboard.fromJSONFile(SEED_PATH)
    if starboard is None:
        raise SystemExit(f"{SEED_PATH} not found: the solve needs it as the CP-SAT hint seed.")

    optimizeKeyboard(starboard, dictionary.syllabicPartAmbiguity, ["onset", "nucleus", "coda"])
    if not starboard.phonemesAssignedToStroke:
        raise SystemExit("optimizeKeyboard produced no layout (no solution found); nothing written.")

    overwritingSeed = os.path.abspath(args.output) == os.path.abspath(SEED_PATH)
    if overwritingSeed:
        print(f"WARNING: overwriting the committed seed layout {SEED_PATH} "
              "(--output was given explicitly).", file=sys.stderr, flush=True)
    starboard.toJSONFile(args.output)
    print(f"\nWrote the optimized layout to {args.output}.")
    if not overwritingSeed:
        print(f"To adopt it: cp {args.output} {SEED_PATH} (deliberate), then:")
    print("  rm -f Dictionary.pickle PhoneticTheory.pickle && python -m util.build_phonetic_theory\n"
          "  (the phonetic theory depends on the layout; every exporter recomputes the"
          " disambiguated theory on its next run).")


if __name__ == "__main__":
    main()
