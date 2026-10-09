#!/usr/bin/env python
# coding: utf-8
"""Tests for lexicon integrity checking."""

import pytest
from util.check_lexicon_features import (
    check_units,
    check_sounded,
    check_infover,
    check_excluded,
    check_participle,
    check_columns,
    check_file,
    check_duplicate_identity,
)


class TestCheckUnits:
    """Test the check_units function."""

    def test_good_units(self) -> None:
        """Test a good row with matching units."""
        syll_cv = "a|b_c"
        orthosyll_cv = "a|b_c"
        assert check_units(syll_cv, orthosyll_cv) is True

    def test_bad_units_count(self) -> None:
        """Test mismatched unit counts."""
        syll_cv = "a|b_c"
        orthosyll_cv = "a|b"
        assert check_units(syll_cv, orthosyll_cv) is False

    def test_bad_units_empty(self) -> None:
        """Test empty units."""
        syll_cv = "a||b"
        orthosyll_cv = "a||b"
        assert check_units(syll_cv, orthosyll_cv) is False


class TestCheckSounded:
    """Test the check_sounded function."""

    def test_good_sounded(self) -> None:
        """Test a good sounded match."""
        syll_cv = "a|b_c"
        phon = "abc"
        assert check_sounded(syll_cv, phon) is True

    def test_bad_sounded(self) -> None:
        """Test mismatched sounded."""
        syll_cv = "a|b_c"
        phon = "ab"
        assert check_sounded(syll_cv, phon) is False

    def test_sounded_with_hash(self) -> None:
        """Test that # is ignored in sounded."""
        syll_cv = "a|#|b_c"
        phon = "abc"
        assert check_sounded(syll_cv, phon) is True


class TestCheckInfover:
    """Test the check_infover function."""

    def test_non_ver(self) -> None:
        """Test that non-VER rows pass."""
        assert check_infover("anything", "NOM")[0] is True

    def test_good_infover(self) -> None:
        """Test a good VER infover."""
        valid, msg = check_infover("ind:pre:1s;", "VER")
        assert valid is True

    def test_empty_infover(self) -> None:
        """Test empty infover for VER."""
        valid, msg = check_infover("", "VER")
        assert valid is False

    def test_infover_missing_semicolon(self) -> None:
        """Test infover missing trailing semicolon."""
        valid, msg = check_infover("ind:pre:1s", "VER")
        assert valid is False

    def test_invalid_infover_tag(self) -> None:
        """Test invalid tag in infover."""
        valid, msg = check_infover("invalid:tag;", "VER")
        assert valid is False


class TestCheckExcluded:
    """Test the check_excluded function."""

    def test_good_excluded(self) -> None:
        """Test that non-sub:imp tags are fine."""
        valid, msg = check_excluded("ind:pre:1s;", "VER")
        assert valid is True

    def test_bad_excluded(self) -> None:
        """Test that sub:imp tags fail."""
        valid, msg = check_excluded("sub:imp:1s;", "VER")
        assert valid is False


class TestCheckParticiple:
    """Test the check_participle function."""

    def test_non_participle(self) -> None:
        """Test non-participle rows pass."""
        valid, msg = check_participle("ind:pre:1s;", None, None, "VER")
        assert valid is True

    def test_good_participle(self) -> None:
        """Test a good participle."""
        valid, msg = check_participle("par:pas;", "m", "s", "VER")
        assert valid is True

    def test_bad_participle_genre(self) -> None:
        """Test participle with invalid genre."""
        valid, msg = check_participle("par:pas;", "n", "s", "VER")
        assert valid is False

    def test_bad_participle_nombre(self) -> None:
        """Test participle with invalid nombre."""
        valid, msg = check_participle("par:pas;", "m", "d", "VER")
        assert valid is False

    def test_participle_with_other_tags(self) -> None:
        """Test participle with other tags (should skip)."""
        valid, msg = check_participle("par:pas;ind:pre:1s;", "n", "d", "VER")
        assert valid is True


class TestCheckColumns:
    """Test the check_columns function."""

    def test_good_columns(self) -> None:
        """Test correct column count."""
        row = {
            "ortho": "a",
            "phon": "a",
            "lemme": "avoir",
            "cgram": "AUX",
            "cgramortho": "NOM,AUX,VER",
            "genre": "",
            "nombre": "",
            "infover": "ind:pre:3s;",
            "syll_cv": "a",
            "orthosyll_cv": "a",
            "freqlivres": "2926.69",
            "freqfilms2": "6350.91",
        }
        assert check_columns(row, 12) is True

    def test_bad_columns(self) -> None:
        """Test incorrect column count."""
        row = {"ortho": "a", "phon": "a"}
        assert check_columns(row, 12) is False


class TestRealFiles:
    """Test on real lexicon files."""

    def test_real_files_basic_checks(self) -> None:
        """Test that real files have no failures on checks 1, 3, 6."""
        # Check Mixte
        mixte_results = check_file("resources/LexiqueMixte.tsv", max_examples=0)
        assert (
            mixte_results["columns"]["FAIL"] == 0
        ), f"Mixte has {mixte_results['columns']['FAIL']} column failures"
        assert (
            mixte_results["excluded"]["FAIL"] == 0
        ), f"Mixte has {mixte_results['excluded']['FAIL']} excluded failures"

        # Check Synthetic
        synthetic_results = check_file(
            "resources/LexiqueSynthetic.tsv", max_examples=0, is_synthetic=True
        )
        assert (
            synthetic_results["columns"]["FAIL"] == 0
        ), f"Synthetic has {synthetic_results['columns']['FAIL']} column failures"
        assert (
            synthetic_results["excluded"]["FAIL"] == 0
        ), f"Synthetic has {synthetic_results['excluded']['FAIL']} excluded failures"

        # Note: duplicateIdentity is a warning, not a failure, so we don't assert on it

    def test_real_files_print_checks_2_4(self) -> None:
        """Print counts for checks 2 and 4 (may have known issues)."""
        mixte_results = check_file("resources/LexiqueMixte.tsv", max_examples=0)
        synthetic_results = check_file(
            "resources/LexiqueSynthetic.tsv", max_examples=0, is_synthetic=True
        )

        print("\nCheck 2 (units) failures:")
        print(f"  Mixte: {mixte_results['units'].get('FAIL', 0)}")
        print(f"  Synthetic: {synthetic_results['units'].get('FAIL', 0)}")

        print("\nCheck 4 (infover) failures:")
        print(f"  Mixte: {mixte_results['infover'].get('FAIL', 0)}")
        print(f"  Synthetic: {synthetic_results['infover'].get('FAIL', 0)}")

        print("\nCheck 5 (participle) warnings:")
        print(f"  Mixte: {mixte_results['participle'].get('WARN', 0)}")
        print(f"  Synthetic: {synthetic_results['participle'].get('WARN', 0)}")

        print("\nCheck 8 (features) failures:")
        print(f"  Mixte: {mixte_results['features'].get('FAIL', 0)}")
        print(f"  Synthetic: {synthetic_results['features'].get('FAIL', 0)}")
