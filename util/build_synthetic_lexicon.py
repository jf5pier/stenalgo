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
TODO.md item TOD13): if it trips, investigate the appenders' reports instead of
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
import shutil
import subprocess
import sys
import tempfile
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


# S2_PROFILE_DIR=DIR: run every step under cProfile and leave DIR/roundN_stepM.prof (read with `python -m pstats`).
PROFILE_DIR_ENV = "S2_PROFILE_DIR"
_currentRound = 0
_stepCounter = 0


def _runStep(description: str, args: list[str]) -> None:
    """Run one step as a subprocess; abort on failure (same semantics as
    dictionary.runStep, kept local so this module need not import dictionary). Every step is timed
    (pipeline_timings.log, kind `step`, labelled with the round)."""
    global _stepCounter
    _stepCounter += 1
    profileDir = os.environ.get(PROFILE_DIR_ENV)
    if profileDir and len(args) > 2 and args[1] == "-m":
        os.makedirs(profileDir, exist_ok=True)
        profileFile = os.path.join(profileDir, f"round{_currentRound}_step{_stepCounter:02d}.prof")
        args = [args[0], "-m", "cProfile", "-o", profileFile, *args[1:]]
    print(f"\n=== Synthetic Lexicon Building (S2): {description} ===\n$ {' '.join(args)}", flush=True)
    with timedCall("step", f"util.build_synthetic_lexicon: round {_currentRound}: {description}"):
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


# S2_SNAPSHOT_DIR=DIR: copy the Synthetic file after every appender (DIR/roundN_stepM.tsv), to see what each step of
# each round added (diff two snapshots).
SNAPSHOT_DIR_ENV = "S2_SNAPSHOT_DIR"
# Whether the file on disk is already pruned and sorted (what the pair of steps after an appender leaves): from then
# on an appender that changed nothing leaves nothing to prune or sort. False at the start, since an --incremental run
# starts from whatever the file holds.
_fileNormalized = False


def runAppendersOnce(forcedRules: Sequence[str] = ()) -> None:
    global _fileNormalized
    snapshotDir = os.environ.get(SNAPSHOT_DIR_ENV)
    for stepNumber, (label, modArgs) in enumerate(S2_APPENDERS, start=1):
        extra: list[str] = []
        if modArgs[1] == "util.completeVerbParadigms":
            for spec in forcedRules:
                extra += ["--force-rule", spec]
        before = _md5(SYNTHETIC_TSV_PATH)
        _runStep(label, [sys.executable, *modArgs, *extra])
        if _fileNormalized and _md5(SYNTHETIC_TSV_PATH) == before:
            continue  # the appender appended nothing: the file is still the pruned, sorted file of the step before
        # The generators know nothing of resources/spellingVariants.tsv (dissous, a form
        # of dissoudre the project drops for dissout, is regenerated every round otherwise):
        # prune the dropped spellings as the loader does, so the round converges. Sorted after each
        # appender that wrote, not once per round: the next appender reads the file (a slot held by two rows is
        # won by the later one), and the order the appenders wrote in varies with the string hash seed.
        _runStep("Synthetic Lexicon Building (S2): prune dropped variant spellings",
                 [sys.executable, "-m", "util.prune_spelling_variants", "--apply"])
        with timedCall("phase", f"util.build_synthetic_lexicon: round {_currentRound}: sort the Synthetic file"):
            canonicalizeSynthetic()
        _fileNormalized = True
        if snapshotDir:
            os.makedirs(snapshotDir, exist_ok=True)
            shutil.copyfile(SYNTHETIC_TSV_PATH, os.path.join(snapshotDir, f"round{_currentRound}_step{stepNumber}.tsv"))


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
    # One state file for the length of this run, for the appenders that can tell a later round has nothing new for them
    # (util.generateMissingNomAdjForms: STATE_ENV); gone when the run ends, so nothing outlives the run it was made in.
    stateDir = tempfile.mkdtemp(prefix="s2_state_")
    os.environ["S2_NOMADJ_STATE"] = os.path.join(stateDir, "nomadj.state")
    try:
        _runRounds(args)
    finally:
        shutil.rmtree(stateDir, ignore_errors=True)


def _runRounds(args: argparse.Namespace) -> None:
    global _currentRound
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
        _currentRound = roundsDone + 1
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
                  "-- the appenders keep appending rows (non-idempotence, cf. TODO.md item TOD13). "
                  "Investigate the reports above instead of raising MAX_ROUNDS.",
                  file=sys.stderr, flush=True)
            raise SystemExit(1)
        changed = True
        print("\nLexiqueSynthetic.tsv changed -- deleting the pickles and rebuilding "
              "Dictionary/phonetic theory...", flush=True)
        for picklePath in PICKLE_CACHE_PATHS:
            if os.path.exists(picklePath):
                os.remove(picklePath)
        # Between rounds only S2.1 reads the theory (PhoneticTheory.pickle): the light rebuild writes that alone.
        _runStep("Phonetic theory (S3-S5), light rebuild between rounds (PhoneticTheory.pickle only)",
                 [sys.executable, "-m", "util.build_phonetic_theory", "--theory-only"])

    if changed:
        # The final state must be what a full build gives: Dictionary.pickle, PhoneticTheory.pickle, phonetic_theory.tsv.
        for picklePath in PICKLE_CACHE_PATHS:
            if os.path.exists(picklePath):
                os.remove(picklePath)
        _runStep("Dictionary loading + phonetic theory (S3-S5), full rebuild after the last append",
                 [sys.executable, "-m", "util.build_phonetic_theory"])
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
