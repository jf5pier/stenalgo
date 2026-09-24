"""
Synthetic Lexicon Building (S2) as one command: run the four steady-state
appenders (`--apply`) until they converge, so the "cascading rounds" happen
inside a single invocation instead of a hand-repeated `python dictionary.py`.

Convergence rule: a full round over the four appenders that leaves
resources/LexiqueSynthetic.tsv byte-identical (md5) has appended nothing --
Synthetic Lexicon Building (S2) is done. After any round that DID append rows,
the pickles are stale, so this module deletes Dictionary.pickle /
PhoneticTheory.pickle and reruns the Dictionary Loading (S3) + Phonetic Theory
Building (S5) build itself (`python -m util.build_phonetic_theory`); the
next round's appenders then see fresh theory, exactly like today's "run it a
second time" convergence. On an already-converged tree nothing is deleted and
no rebuild runs.

MAX_ROUNDS guards against the appenders never converging (non-idempotence,
TODO.md item B13): if it trips, investigate the appenders' reports instead of
raising the cap.

Run: python -m util.build_synthetic_lexicon   (from the repo root; it chdirs there)
Requires resources/LexiqueMixte.tsv; S2.1 additionally wants PhoneticTheory.pickle
(it rebuilds theory in memory when absent, without persisting).
Exit codes: 0 converged; 1 an appender or rebuild failed, or MAX_ROUNDS tripped.
"""
import hashlib
import os
import subprocess
import sys

SYNTHETIC_TSV_PATH = "resources/LexiqueSynthetic.tsv"
PICKLE_CACHE_PATHS = ("Dictionary.pickle", "PhoneticTheory.pickle")

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


def runAppendersOnce() -> None:
    for label, modArgs in S2_APPENDERS:
        _runStep(label, [sys.executable, *modArgs])


def main() -> None:
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    changed = False
    roundsDone = 0
    while True:
        before = _md5(SYNTHETIC_TSV_PATH)
        runAppendersOnce()
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
              "`rm -f Dictionary.pickle PhoneticTheory.pickle` and re-run).", flush=True)


if __name__ == "__main__":
    main()
