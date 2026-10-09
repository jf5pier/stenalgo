"""Unit tests for util/build_synthetic_lexicon.py: the convergence loop's pure
decision function and the invariants of the moved S2_APPENDERS/constants."""
from util.build_synthetic_lexicon import (
    MAX_ROUNDS,
    PICKLE_CACHE_PATHS,
    S2_APPENDERS,
    SYNTHETIC_HEADER,
    SYNTHETIC_TSV_PATH,
    canonicalizeSynthetic,
    nextRoundAction,
    resetToHeader,
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

def test_appenders_are_the_five_steady_state_modules():
    modules = {modArgs[1] for _, modArgs in S2_APPENDERS}
    assert modules == {
        "util.completeVerbParadigms",
        "util.generateMissingNomAdjForms",
        "util.fixPayerDualFormGaps",
        "util.fixAsseoirDualFormGaps",
        "util.appendSyntheticManualRows",
    }


def test_every_appender_runs_with_apply():
    assert len(S2_APPENDERS) == 5
    for label, modArgs in S2_APPENDERS:
        assert isinstance(label, str) and label
        assert isinstance(modArgs, list)
        assert modArgs[-1] == "--apply"


def test_moved_constants_keep_their_values():
    # These moved from dictionary.py; pin them so the move cannot silently drift.
    # DisambiguatedTheory.pickle joined the S2 deletion set 2026-09-29 (fingerprinted
    # cache, util/_theoryio.py; would self-invalidate anyway, deleted to keep step).
    assert PICKLE_CACHE_PATHS == ("Dictionary.pickle", "PhoneticTheory.pickle",
                                  "DisambiguatedTheory.pickle")
    assert SYNTHETIC_TSV_PATH == "resources/LexiqueSynthetic.tsv"


# ── from-scratch reset and canonical order ───────────────────────────────────

def test_reset_to_header_empties_the_file_and_deletes_the_pickles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    synthetic = tmp_path / "LexiqueSynthetic.tsv"
    synthetic.write_bytes(b"ortho\tphon\r\nb\tx\r\na\ty\n")
    for name in PICKLE_CACHE_PATHS:
        (tmp_path / name).write_text("stale")
    dropped = resetToHeader(str(synthetic))
    assert dropped == 2
    assert synthetic.read_bytes() == b"ortho\tphon\n"  # header kept, its CRLF normalized
    assert not any((tmp_path / name).exists() for name in PICKLE_CACHE_PATHS)


def test_reset_to_header_creates_a_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "LexiqueSynthetic.tsv"
    assert resetToHeader(str(path)) == 0
    assert path.read_text() == SYNTHETIC_HEADER


def test_canonicalize_sorts_data_lines_and_keeps_the_header(tmp_path):
    path = tmp_path / "s.tsv"
    path.write_text("ortho\tphon\nb\t2\na\t1\nc\t3\n")
    canonicalizeSynthetic(str(path))
    assert path.read_text() == "ortho\tphon\na\t1\nb\t2\nc\t3\n"
    canonicalizeSynthetic(str(path))  # idempotent
    assert path.read_text() == "ortho\tphon\na\t1\nb\t2\nc\t3\n"
