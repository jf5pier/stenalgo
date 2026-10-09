"""
Synthetic Lexicon Building (S2) as one command: run the four steady-state
appenders (`--apply`) until they converge, so the "cascading rounds" happen
inside a single invocation instead of a hand-repeated `python dictionary.py`.

Convergence rule: a full round over the four appenders that leaves
resources/LexiqueSynthetic.tsv byte-identical (md5) has appended nothing --
Synthetic Lexicon Building (S2) is done. After any round that DID append rows,
the pickles are stale, so this module deletes the pickle caches
(PICKLE_CACHE_PATHS: Dictionary.pickle / PhoneticTheory.pickle /
DisambiguatedTheory.pickle) and reruns the Dictionary Loading (S3) + Phonetic Theory
Building (S5) build itself (`python -m util.build_phonetic_theory`); the
next round's appenders then see fresh theory, exactly like today's "run it a
second time" convergence. On an already-converged tree nothing is deleted and
no rebuild runs.

MAX_ROUNDS guards against the appenders never converging (non-idempotence,
TODO.md item B13): if it trips, investigate the appenders' reports instead of
raising the cap.

From scratch by default: the Synthetic file is emptied to its header first, so it is a pure function of
Lexique383, Infra, Verbiste, LexiqueMixte.tsv, the spelling-variant rulings, the Morphalou distillate and
resources/syntheticManualRows.tsv. --incremental keeps the existing rows.

Run: python -m util.build_synthetic_lexicon [--incremental]   (from the repo root; it chdirs there)
Requires resources/LexiqueMixte.tsv; S2.1 additionally wants PhoneticTheory.pickle
(it rebuilds theory in memory when absent, without persisting).
Exit codes: 0 converged; 1 an appender or rebuild failed, or MAX_ROUNDS tripped.
"""
import argparse
import hashlib
import os
import subprocess
import sys
from collections.abc import Sequence

from util._timing import timedCall

SYNTHETIC_TSV_PATH = "resources/LexiqueSynthetic.tsv"
# DisambiguatedTheory.pickle is fingerprint-checked (util/_theoryio.py) and would
# self-invalidate on the LexiqueSynthetic.tsv md5 change anyway; deleting it here
# keeps the three caches in step.
PICKLE_CACHE_PATHS = ("Dictionary.pickle", "PhoneticTheory.pickle", "DisambiguatedTheory.pickle")

# The steady-state Synthetic Lexicon Building (S2) appenders, run with --apply (their
# dry-run mode is for a human checking a diff first). The one-shot fix scripts stay
# hand-run; see docs/PIPELINE.md Synthetic Lexicon Building (S2).
S2_APPENDERS: list[tuple[str, list[str]]] = [
    ("Synthetic Lexicon Building (S2.1): verb paradigm completion",
     ["-m", "util.completeVerbParadigms", "--apply"]),
    ("Synthetic Lexicon Building (S2.2): NOM/ADJ gap generation",
     ["-m", "util.generateMissingNomAdjForms", "--apply"]),
    ("Synthetic Lexicon Building (S2.3): pa:yer dual-form gaps",
     ["-m", "util.fixPayerDualFormGaps", "--apply"]),
    ("Synthetic Lexicon Building (S2.3): ass:eoir dual-form gaps",
     ["-m", "util.fixAsseoirDualFormGaps", "--apply"]),
    ("Synthetic Lexicon Building (S2.4): hand-derived rows (resources/syntheticManualRows.tsv)",
     ["-m", "util.appendSyntheticManualRows", "--apply"]),
]

MAX_ROUNDS = 10


def _md5(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _runStep(description: str, args: list[str]) -> None:
    """Run one step as a subprocess; abort on failure (same semantics as
    dictionary.runStep, kept local so this module need not import dictionary)."""
    print(f"\n=== Synthetic Lexicon Building (S2): {description} ===\n$ {' '.join(args)}", flush=True)
    completed = subprocess.run(args)
    if completed.returncode != 0:
        print(f"\nSynthetic Lexicon Building (S2) step FAILED: {description}\n"
              f"  command: {' '.join(args)}\n  exit code: {completed.returncode}\n"
              "Fix the problem above, then re-run `python -m util.build_synthetic_lexicon` "
              "(or `python dictionary.py`).",
              file=sys.stderr, flush=True)
        raise SystemExit(completed.returncode or 1)


def nextRoundAction(roundsDone: int, tsvChangedThisRound: bool, maxRounds: int = MAX_ROUNDS) -> str:
    """Pure loop decision: 'converged' (last round appended nothing -- stop),
    'abort' (still appending at the cap -- give up loudly), 'rerun' (rows were
    appended -- invalidate and go again)."""
    if not tsvChangedThisRound:
        return "converged"
    if roundsDone >= maxRounds:
        return "abort"
    return "rerun"


def canonicalizeSynthetic(path: str = SYNTHETIC_TSV_PATH) -> None:
    """Sort the data lines (header first) so the file does not depend on the appenders'
    set/dict iteration order, which varies with the string hash seed between runs."""
    with open(path, encoding="utf-8", newline="") as f:
        lines = f.read().split("\n")
    trailing = lines[-1] == ""
    body = lines[:-1] if trailing else lines
    header, rows = body[:1], sorted(body[1:])
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(header + rows) + ("\n" if trailing else ""))


def runAppendersOnce(forcedRules: Sequence[str] = ()) -> None:
    for label, modArgs in S2_APPENDERS:
        extra: list[str] = []
        if modArgs[1] == "util.completeVerbParadigms":
            for spec in forcedRules:
                extra += ["--force-rule", spec]
        _runStep(label, [sys.executable, *modArgs, *extra])
        # The generators know nothing of resources/spellingVariants.tsv (dissous, a form
        # of dissoudre the project drops for dissout, is regenerated every round otherwise):
        # prune the dropped spellings as the loader does, so the round converges.
        _runStep("Synthetic Lexicon Building (S2): prune dropped variant spellings",
                 [sys.executable, "-m", "util.prune_spelling_variants", "--apply"])
        canonicalizeSynthetic()


SYNTHETIC_HEADER = (
    "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\t"
    "syll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2\tsource\n"
)


def resetToHeader(path: str = SYNTHETIC_TSV_PATH) -> int:
    """Empty the Synthetic file down to its header (written if the file is absent) and delete the pickle
    caches built on the old rows; returns the number of data rows dropped."""
    dropped = 0
    header = SYNTHETIC_HEADER
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as f:
            first = f.readline()
            dropped = sum(1 for line in f if line.strip())
        if first.strip():
            header = first.rstrip("\r\n") + "\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(header)
    for picklePath in PICKLE_CACHE_PATHS:
        if os.path.exists(picklePath):
            os.remove(picklePath)
    return dropped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--incremental", action="store_true",
                        help="Keep the rows already in resources/LexiqueSynthetic.tsv (the former append-only "
                        "behaviour). Default: rebuild the file from scratch, as a pure function of its inputs.")
    parser.add_argument("--force-rule", action="append", default=[], metavar="NAME[=PARAM]",
                        help="Run a synthesis mechanism of src/synthrules.py without an accepted decision "
                        "(passed to util.completeVerbParadigms), e.g. reference-bar[=FLOOR].")
    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not args.incremental:
        dropped = resetToHeader()
        print(f"From scratch: {SYNTHETIC_TSV_PATH} emptied to its header ({dropped} rows dropped), pickles deleted.",
              flush=True)
    changed = False
    roundsDone = 0
    while True:
        before = _md5(SYNTHETIC_TSV_PATH)
        # Per-round phase lines: the whole S2 step logs only one "step" line, so
        # round-level costs (which round appended, how long the scans took) used
        # to be inferable only from timestamps.
        with timedCall("phase", f"util.build_synthetic_lexicon: appender round {roundsDone + 1}"):
            runAppendersOnce(args.force_rule)
        roundsDone += 1
        action = nextRoundAction(roundsDone, _md5(SYNTHETIC_TSV_PATH) != before)
        if action == "converged":
            print(f"\nSynthetic Lexicon Building (S2) converged after {roundsDone} round(s) "
                  "(the last round appended nothing).", flush=True)
            break
        if action == "abort":
            print(f"\nSynthetic Lexicon Building (S2) DID NOT converge after {roundsDone} rounds "
                  "-- the appenders keep appending rows (non-idempotence, cf. TODO.md item B13). "
                  "Investigate the reports above instead of raising MAX_ROUNDS.",
                  file=sys.stderr, flush=True)
            raise SystemExit(1)
        changed = True
        print("\nLexiqueSynthetic.tsv changed -- deleting the pickles and rebuilding "
              "Dictionary/phonetic theory...", flush=True)
        for picklePath in PICKLE_CACHE_PATHS:
            if os.path.exists(picklePath):
                os.remove(picklePath)
        _runStep("Dictionary loading + phonetic theory (S3-S5), post-append rebuild",
                 [sys.executable, "-m", "util.build_phonetic_theory"])

    if changed:
        print("Next: `python -m src.elicitation --resolve` (after any re-elicitation), then "
              "`python -m util.build_disambiguated_theory` to refresh disambiguated_theory.tsv, then the exports.",
              flush=True)
    else:
        print("\nLexiqueSynthetic.tsv unchanged -- keeping the existing pickles "
              "(if you edited the lexicons or layout since they were written, "
              "`rm -f Dictionary.pickle PhoneticTheory.pickle DisambiguatedTheory.pickle` "
              "and re-run).", flush=True)


if __name__ == "__main__":
    main()
