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
    verbLines = [line for line in manualLines if line.split("\t")[3] == "VER"]
    elisionLines = [line for line in manualLines if line.split("\t")[0].endswith("'")]
    assert len(verbLines) == 218  # the 21 asseoir rows + 197 rows promoted from the pre-regeneration file (2026-10-10)
    assert len(elisionLines) == 9  # j' c' qu'(x2) jusqu' lorsqu' puisqu' quoiqu' presqu': the elided forms Lexique383 lacks
    assert len(manualLines) == len(verbLines) + len(elisionLines)
    assert sum(line.split("\t")[2] in ("asseoir", "rasseoir") for line in manualLines) == 21
    for line in manualLines:
        fields = line.split("\t")
        assert len(fields) == len(manualHeader.split("\t"))
        assert fields[-1] == "synthetic" and (fields[3] == "VER" or fields[0].endswith("'"))
        assert len(fields[8].split("|")) == len(fields[9].split("|"))
