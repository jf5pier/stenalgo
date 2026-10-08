"""Unit tests for the number lessons (`util/number_lessons.py`): how a number splits into strokes in each style."""

import unittest

from util.number_lessons import expandTokens, glueChords, lapwingSplit, numberEntries, pluvierSplit


class TestSplit(unittest.TestCase):
    def test_pluvier_runs_go_up_in_the_keyboard_order(self) -> None:
        self.assertEqual(pluvierSplit("12346789"), ["12346789"])         # 5 and 0 are missing but the order holds
        self.assertEqual(pluvierSplit("50"), ["50"])                       # 5 then 0 (0 sits after 5)
        self.assertEqual(pluvierSplit("80"), ["8", "0"])                   # 0 comes before 8 in the order: two strokes
        self.assertEqual(pluvierSplit("2025"), ["20", "25"])
        self.assertEqual(pluvierSplit("11"), ["1", "1"])                   # strictly: a key is not pressed twice

    def test_lapwing_groups_a_digit_with_its_zeros(self) -> None:
        self.assertEqual(lapwingSplit("2025"), ["20", "2", "5"])
        self.assertEqual(lapwingSplit("1000"), ["1000"])
        self.assertEqual(lapwingSplit("1000000"), ["1000", "000"])
        self.assertEqual(lapwingSplit("1005"), ["100", "5"])
        self.assertEqual(lapwingSplit("0"), ["0"])
        self.assertEqual(lapwingSplit("1990"), ["1", "9", "90"])


class TestEntries(unittest.TestCase):
    def test_glue_chords_keep_the_plain_glues_only(self) -> None:
        chords = glueChords({"-#s": "{&1}", "i#s": "{&10}", "a#m": "{&00}", "e#": "{&00}", "pi#": "{^ ^}{&0}", "x": "10 h"})
        self.assertEqual(chords, {"1": ["-#s"], "10": ["i#s"], "00": ["e#", "a#m"]})

    def test_expand_tokens_replaces_a_number_by_its_strokes(self) -> None:
        entries = numberEntries({"20": ["pa#"], "25": ["p@#"]})
        self.assertEqual(expandTokens("bar", ["en", "#2025"], entries), ["en", "@n_20", "@n_25"])
        with self.assertRaises(ValueError):
            expandTokens("bar", ["#7"], entries)


if __name__ == "__main__":
    unittest.main()
