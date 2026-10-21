"""
Keyboard Layout Optimization (S4) as a command: the CP-SAT phoneme-to-key
layout solve, runnable without editing code.

Run: python -m util.optimize_keyboard [--output PATH] [--statistics PATH] [--parts onset nucleus coda] [--time SECONDS] [--workers N]
                                      [--seed N] [--log] [--incumbent-dir DIR] [--report PATH] [--seed-layout PATH]   (from the repo root)
--statistics PATH solves on the layout statistics file of `python -m util.build_layout_statistics` (rewritten phonology, typed frequencies)
instead of Dictionary.pickle; it is self-contained, so nothing else of the lexicon side is needed.
Remote run: one process per part (`--parts onset`, `--parts coda`), each with its own --output, --workers and --time; a partial output holds only its
parts' strokes and is combined with `python -m util.merge_layouts`. --incumbent-dir keeps the best solution found so far of each part
(`DIR/incumbent_<part>.json`, a layout file, rewritten every few seconds) so a killed run loses nothing; --report writes status, objective, best bound and
relative gap per part (a gap of 0 means converged).
--seed-layout PATH hints from another layout than starboard3h.json (a hint only: the search does not restart from its cost). After a crash the
incumbent files ARE the result: combine them with util.merge_layouts. Defaults are the historical ones: all parts, 90 s each, every core, quiet.
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
from typing import TYPE_CHECKING

from src.cpsatsolver import SolverSettings, optimizeKeyboard
from src.keyboard import Starboard
from src.layoutstatistics import loadLayoutStatistics

if TYPE_CHECKING:
    from dictionary import Dictionary

SEED_PATH = "starboard3h.json"
PARTS = ("onset", "nucleus", "coda")
DEFAULT_OUTPUT = "starboard3h_optimized.json"


def parseArgs(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m util.optimize_keyboard",
        description="Keyboard Layout Optimization (S4): the CP-SAT layout solve, seeded from "
                    f"{SEED_PATH}.")
    parser.add_argument("--output", metavar="PATH", default=DEFAULT_OUTPUT,
                        help=f"where to write the solved layout (default: {DEFAULT_OUTPUT}; "
                             f"{SEED_PATH} is overwritten only if passed explicitly)")
    parser.add_argument("--statistics", metavar="PATH", default=None,
                        help="layout statistics file (util.build_layout_statistics) to solve on; default: Dictionary.pickle")
    parser.add_argument("--parts", nargs="+", choices=PARTS, default=list(PARTS), metavar="PART",
                        help="syllabic parts to solve (default: onset nucleus coda); a subset gives a partial layout, see util.merge_layouts")
    parser.add_argument("--seed-layout", metavar="PATH", default=SEED_PATH,
                        help=f"layout the solver hints from (default {SEED_PATH}). Only a hint: CP-SAT does not restart from it at its cost, so this does not resume a run")
    parser.add_argument("--time", type=float, default=SolverSettings.timeSeconds, metavar="SECONDS",
                        help="solver time limit PER PART (default: %(default)s)")
    parser.add_argument("--workers", type=int, default=0, metavar="N", help="solver threads (default 0: every core)")
    parser.add_argument("--seed", type=int, default=None, metavar="N", help="solver random seed (default: the solver's own)")
    parser.add_argument("--log", action="store_true", help="print the solver's search log")
    parser.add_argument("--incumbent-dir", metavar="DIR", default=None,
                        help="keep the best solution so far of each part as DIR/incumbent_<part>.json")
    parser.add_argument("--report", metavar="PATH", default=None, help="write status, objective, best bound and gap per part (JSON)")
    return parser.parse_args(argv)


def _buildDictionaryInMemory() -> "Dictionary":
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
    overwritingSeed = os.path.abspath(args.output) == os.path.abspath(SEED_PATH)
    partial = set(args.parts) != set(PARTS)
    if partial and overwritingSeed:
        raise SystemExit(f"--parts {' '.join(args.parts)} gives a partial layout: it cannot overwrite {SEED_PATH}; "
                         "write it elsewhere and combine the parts with `python -m util.merge_layouts`.")
    if args.statistics is not None:
        envelope = loadLayoutStatistics(args.statistics)
        syllabicPartAmbiguity = envelope["tables"]["syllabicPartAmbiguity"]
        print(f"Layout statistics from {args.statistics}: {envelope['meta']['words']} words, "
              f"phonology rewrite {'on' if envelope['meta']['rewrite'] else 'off'}.")
    else:
        from util._theoryio import loadDictionary  # lazy: --statistics needs none of the lexicon side (the remote machine has only src/)
        dictionary = loadDictionary() if os.path.exists("Dictionary.pickle") else _buildDictionaryInMemory()
        dictionary.ensureAmbiguityStats()  # Dictionary.pickle no longer carries them (util.build_phonetic_theory skips them)
        syllabicPartAmbiguity = dictionary.syllabicPartAmbiguity

    starboard = Starboard.fromJSONFile(args.seed_layout)
    if starboard is None:
        raise SystemExit(f"{args.seed_layout} not found: the solve needs it as the CP-SAT hint seed.")

    incumbentPath = None
    if args.incumbent_dir is not None:
        os.makedirs(args.incumbent_dir, exist_ok=True)
        incumbentPath = os.path.join(args.incumbent_dir, "incumbent_{part}.json")
    settings = SolverSettings(timeSeconds=args.time, workers=args.workers, seed=args.seed, log=args.log,
                              incumbentPath=incumbentPath, reportPath=args.report)
    optimizeKeyboard(starboard, syllabicPartAmbiguity, list(args.parts), settings)
    if not starboard.phonemesAssignedToStroke:
        raise SystemExit("optimizeKeyboard produced no layout (no solution found); nothing written.")

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
