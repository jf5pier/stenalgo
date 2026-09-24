"""Unit tests for util/build_synthetic_lexicon.py: the convergence loop's pure
decision function and the invariants of the moved S2_APPENDERS/constants."""
from util.build_synthetic_lexicon import (
    MAX_ROUNDS,
    PICKLE_CACHE_PATHS,
    S2_APPENDERS,
    SYNTHETIC_TSV_PATH,
    nextRoundAction,
)


# ── nextRoundAction ──────────────────────────────────────────────────────────

def test_unchanged_round_converges():
    assert nextRoundAction(1, False) == "converged"


def test_changed_round_below_cap_reruns():
    assert nextRoundAction(1, True) == "rerun"
    assert nextRoundAction(MAX_ROUNDS - 1, True) == "rerun"


def test_changed_round_at_cap_aborts():
    assert nextRoundAction(MAX_ROUNDS, True) == "abort"


def test_converged_round_still_converges_at_cap():
    # A converged round is a success even if it is the round at the cap.
    assert nextRoundAction(MAX_ROUNDS, False) == "converged"


def test_custom_cap_boundary():
    assert nextRoundAction(1, True, maxRounds=1) == "abort"
    assert nextRoundAction(1, False, maxRounds=1) == "converged"


# ── S2_APPENDERS / moved constants ───────────────────────────────────────────

def test_appenders_are_the_four_steady_state_modules():
    modules = {modArgs[1] for _, modArgs in S2_APPENDERS}
    assert modules == {
        "util.completeVerbParadigms",
        "util.generateMissingNomAdjForms",
        "util.fixPayerDualFormGaps",
        "util.fixAsseoirDualFormGaps",
    }


def test_every_appender_runs_with_apply():
    assert len(S2_APPENDERS) == 4
    for label, modArgs in S2_APPENDERS:
        assert isinstance(label, str) and label
        assert isinstance(modArgs, list)
        assert modArgs[-1] == "--apply"


def test_moved_constants_keep_their_values():
    # These moved from dictionary.py; pin them so the move cannot silently drift.
    assert PICKLE_CACHE_PATHS == ("Dictionary.pickle", "FirstTheory.pickle")
    assert SYNTHETIC_TSV_PATH == "resources/LexiqueSynthetic.tsv"
