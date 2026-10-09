"""Unit tests for util/appendSyntheticManualRows.py and the committed resources/syntheticManualRows.tsv."""
from util.appendSyntheticManualRows import MANUAL_ROWS_PATH, SYNTHETIC_PATH, missingRows, readDataLines, rowKey


def _row(ortho: str, lemme: str, infover: str) -> str:
    return "\t".join([ortho, "p", lemme, "VER", "VER", "", "", infover, "s", "o", "0.0", "0.0", "synthetic"])


def test_missing_rows_skips_rows_already_present_by_ortho_lemme_infover():
    manual = [_row("assoyais", "asseoir", "ind:imp:1s;"), _row("assoyions", "asseoir", "ind:imp:1p;")]
    synthetic = [_row("assoyais", "asseoir", "ind:imp:1s;"), _row("other", "x", "inf;")]
    assert missingRows(manual, synthetic) == [manual[1]]


def test_missing_rows_distinguishes_a_different_infover():
    manual = [_row("assoyais", "asseoir", "ind:imp:1s;ind:imp:2s;")]
    assert missingRows(manual, [_row("assoyais", "asseoir", "ind:imp:1s;")]) == manual


def test_missing_rows_is_idempotent_once_appended():
    manual = [_row("a", "l", "x;")]
    assert missingRows(manual, manual) == []


def test_row_key_columns():
    assert rowKey(_row("assoyais", "asseoir", "ind:imp:1s;")) == ("assoyais", "asseoir", "ind:imp:1s;")


def test_committed_manual_rows_have_the_synthetic_header_and_are_well_formed():
    manualHeader, manualLines = readDataLines(MANUAL_ROWS_PATH)
    syntheticHeader, _ = readDataLines(SYNTHETIC_PATH)
    assert manualHeader == syntheticHeader
    assert len(manualLines) == 21
    for line in manualLines:
        fields = line.split("\t")
        assert len(fields) == len(manualHeader.split("\t"))
        assert fields[3] == "VER" and fields[-1] == "synthetic"
        assert fields[2] in ("asseoir", "rasseoir")
